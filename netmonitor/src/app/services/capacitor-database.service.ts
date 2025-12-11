import { DatabaseService } from './database.service';
import { CapacitorSQLite, SQLiteConnection, SQLiteDBConnection } from '@capacitor-community/sqlite';

/**
 * Capacitor/Mobile implementation of DatabaseService using @capacitor-community/sqlite.
 * Database file is stored in app-specific storage automatically.
 */
export class CapacitorDatabaseService extends DatabaseService {
  private sqlite: SQLiteConnection;
  private db: SQLiteDBConnection | null = null;
  // Capacitor SQLite expects name without .db extension (adds it automatically)
  private readonly dbName = this.DB_NAME.replace('.db', '');

  constructor() {
    super();
    this.sqlite = new SQLiteConnection(CapacitorSQLite);
  }

  async init(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      // Check connection consistency
      const retCC = await this.sqlite.checkConnectionsConsistency();
      const isConn = (await this.sqlite.isConnection(this.dbName, false)).result;

      if (retCC.result && isConn) {
        this.db = await this.sqlite.retrieveConnection(this.dbName, false);
      } else {
        this.db = await this.sqlite.createConnection(
          this.dbName,
          false,
          'no-encryption',
          1,
          false
        );
      }

      await this.db.open();
      this.setInitialized(true);
    } catch (error) {
      console.error('CapacitorDatabaseService: Failed to initialize database', error);
      // Don't crash the app - graceful degradation
    }
  }

  async execute(sql: string, params?: unknown[]): Promise<void> {
    if (!this.db) {
      console.warn('CapacitorDatabaseService: Database not initialized');
      return;
    }

    try {
      if (params && params.length > 0) {
        await this.db.run(sql, params as (string | number | boolean | null)[]);
      } else {
        await this.db.execute(sql);
      }
    } catch (error) {
      console.error('CapacitorDatabaseService: Execute failed', error);
      throw error;
    }
  }

  async select<T>(sql: string, params?: unknown[]): Promise<T[]> {
    if (!this.db) {
      console.warn('CapacitorDatabaseService: Database not initialized');
      return [];
    }

    try {
      const result = await this.db.query(sql, params as (string | number | boolean | null)[] | undefined);
      return (result.values ?? []) as T[];
    } catch (error) {
      console.error('CapacitorDatabaseService: Select failed', error);
      throw error;
    }
  }

  async close(): Promise<void> {
    if (!this.db) {
      return;
    }

    try {
      await this.db.close();
      await this.sqlite.closeConnection(this.dbName, false);
      this.db = null;
      this.setInitialized(false);
    } catch (error) {
      console.error('CapacitorDatabaseService: Close failed', error);
    }
  }
}
