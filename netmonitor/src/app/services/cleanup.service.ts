import { inject, Injectable } from '@angular/core';
import { PingRepository } from './ping.repository';

/**
 * Service responsible for cleaning up old monitoring data.
 * Runs on app startup after database migrations.
 */
@Injectable({
  providedIn: 'root'
})
export class CleanupService {
  private readonly pingRepository = inject(PingRepository);

  /**
   * Run data retention cleanup.
   * Deletes monitoring data older than the retention period.
   * This method handles errors internally to avoid blocking app startup.
   */
  async runCleanup(): Promise<void> {
    console.log('CleanupService: Starting data retention cleanup...');

    try {
      await this.pingRepository.deleteOldPings();
      console.log('CleanupService: Cleanup complete');
    } catch (err) {
      console.error('CleanupService: Cleanup failed:', err);
    }
  }
}
