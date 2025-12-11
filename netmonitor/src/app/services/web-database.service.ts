import { DatabaseService } from './database.service';

/**
 * Browser/Web stub implementation of DatabaseService.
 * All methods are no-ops that log warnings. App remains functional without database.
 */
export class WebDatabaseService extends DatabaseService {
  async init(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    console.warn('WebDatabaseService: Database not available in browser');
    // Set initialized to true so app can function without database
    this.setInitialized(true);
  }

  async execute(sql: string, params?: unknown[]): Promise<void> {
    console.warn('WebDatabaseService: Database not available in browser - execute ignored', { sql, params });
  }

  async select<T>(_sql: string, _params?: unknown[]): Promise<T[]> {
    console.warn('WebDatabaseService: Database not available in browser - returning empty array');
    return [];
  }

  async close(): Promise<void> {
    // No-op for browser
  }
}
