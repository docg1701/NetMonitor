import { inject, Injectable } from '@angular/core';
import { DatabaseService } from './database.service';
import { PingResult } from '../models/ping-result.interface';

/** Default data retention period in days */
const DEFAULT_RETENTION_DAYS = 30;

/** Milliseconds in one day */
const MS_PER_DAY = 24 * 60 * 60 * 1000;

/**
 * Repository service for persisting ping results to the database.
 * Handles all database operations related to ping measurements.
 */
@Injectable({
  providedIn: 'root'
})
export class PingRepository {
  private readonly db = inject(DatabaseService);

  /**
   * Persist a ping result to the database.
   * This method is non-blocking and handles errors internally.
   * @param result The ping result to save
   * @param target The target URL that was pinged
   */
  async savePing(result: PingResult, target: string): Promise<void> {
    if (!this.db.isInitialized) {
      return;
    }

    try {
      await this.db.execute(
        'INSERT INTO pings (timestamp, latency_ms, success, target) VALUES (?, ?, ?, ?)',
        [
          result.timestamp.getTime(),
          result.latencyMs,
          result.status === 'ok' ? 1 : 0,
          target
        ]
      );
    } catch (err) {
      console.error('Failed to persist ping:', err);
    }
  }

  /**
   * Delete ping records older than the specified retention period.
   * This method handles errors internally to avoid blocking cleanup operations.
   * @param retentionDays Number of days to retain data (default: 30)
   * @returns Number of deleted records, or 0 if operation fails or DB not initialized
   */
  async deleteOldPings(retentionDays: number = DEFAULT_RETENTION_DAYS): Promise<number> {
    if (!this.db.isInitialized) {
      return 0;
    }

    try {
      const cutoff = Date.now() - (retentionDays * MS_PER_DAY);
      const count = await this.db.executeWithCount(
        'DELETE FROM pings WHERE timestamp < ?',
        [cutoff]
      );
      console.log(`PingRepository: Deleted ${count} old ping records`);
      return count;
    } catch (err) {
      console.error('Failed to delete old pings:', err);
      return 0;
    }
  }
}
