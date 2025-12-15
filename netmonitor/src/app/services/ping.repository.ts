import { inject, Injectable } from '@angular/core';
import { DatabaseService } from './database.service';
import { PingResult } from '../models/ping-result.interface';

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
}
