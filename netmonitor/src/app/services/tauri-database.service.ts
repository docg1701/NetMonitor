import { DatabaseService } from './database.service';
import Database from '@tauri-apps/plugin-sql';

/**
 * Tauri/Desktop implementation of DatabaseService using tauri-plugin-sql.
 * Database file is stored in the app data directory automatically.
 */
export class TauriDatabaseService extends DatabaseService {
  private db: Database | null = null;

  async init(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      this.db = await Database.load(`sqlite:${this.DB_NAME}`);
      this.setInitialized(true);
    } catch (error) {
      console.error('TauriDatabaseService: Failed to initialize database', error);
      // Don't crash the app - graceful degradation
    }
  }

  async execute(sql: string, params?: unknown[]): Promise<void> {
    if (!this.db) {
      console.warn('TauriDatabaseService: Database not initialized');
      return;
    }

    try {
      await this.db.execute(sql, params);
    } catch (error) {
      console.error('TauriDatabaseService: Execute failed', error);
      throw error;
    }
  }

  async select<T>(sql: string, params?: unknown[]): Promise<T[]> {
    if (!this.db) {
      console.warn('TauriDatabaseService: Database not initialized');
      return [];
    }

    try {
      return await this.db.select<T[]>(sql, params) as T[];
    } catch (error) {
      console.error('TauriDatabaseService: Select failed', error);
      throw error;
    }
  }

  async close(): Promise<void> {
    if (!this.db) {
      return;
    }

    try {
      await this.db.close();
      this.db = null;
      this.setInitialized(false);
    } catch (error) {
      console.error('TauriDatabaseService: Close failed', error);
    }
  }
}
