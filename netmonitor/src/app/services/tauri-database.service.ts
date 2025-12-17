import { DatabaseService } from './database.service';
import Database from '@tauri-apps/plugin-sql';

/**
 * Tauri/Desktop implementation of DatabaseService using tauri-plugin-sql.
 * Database file is stored in the app data directory automatically.
 */
export class TauriDatabaseService extends DatabaseService {
  private db: Database | null = null;

  async init(): Promise<void> {
    console.log('TauriDB: init() called, isInitialized:', this.isInitialized);
    if (this.isInitialized) {
      return;
    }

    try {
      console.log('TauriDB: Calling Database.load()...');
      this.db = await Database.load(`sqlite:${this.DB_NAME}`);
      console.log('TauriDB: Database.load() success');
      this.setInitialized(true);
    } catch (error) {
      console.error('TauriDatabaseService: Failed to initialize database', error);
      // Still mark as initialized to allow app to proceed (graceful degradation)
      // DB operations will be no-ops since this.db is null
      this.setInitialized(true);
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

  async executeWithCount(sql: string, params?: unknown[]): Promise<number> {
    if (!this.db) {
      console.warn('TauriDatabaseService: Database not initialized');
      return 0;
    }

    try {
      const result = await this.db.execute(sql, params);
      return result.rowsAffected;
    } catch (error) {
      console.error('TauriDatabaseService: ExecuteWithCount failed', error);
      throw error;
    }
  }
}
