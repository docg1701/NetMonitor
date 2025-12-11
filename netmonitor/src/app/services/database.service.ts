import { BehaviorSubject, Observable } from 'rxjs';

/**
 * Abstract base class for platform-agnostic database operations.
 * Implementations: TauriDatabaseService, CapacitorDatabaseService, WebDatabaseService
 */
export abstract class DatabaseService {
  protected readonly DB_NAME = 'netmonitor.db';

  private readonly _isInitialized$ = new BehaviorSubject<boolean>(false);
  readonly isInitialized$: Observable<boolean> = this._isInitialized$.asObservable();

  protected setInitialized(value: boolean): void {
    this._isInitialized$.next(value);
  }

  get isInitialized(): boolean {
    return this._isInitialized$.getValue();
  }

  /**
   * Initialize database connection.
   * Creates the database file if it doesn't exist.
   */
  abstract init(): Promise<void>;

  /**
   * Execute INSERT/UPDATE/DELETE statements.
   * @param sql SQL statement to execute
   * @param params Optional parameters for prepared statement
   */
  abstract execute(sql: string, params?: unknown[]): Promise<void>;

  /**
   * Execute SELECT queries and return results.
   * @param sql SQL query to execute
   * @param params Optional parameters for prepared statement
   * @returns Array of result rows
   */
  abstract select<T>(sql: string, params?: unknown[]): Promise<T[]>;

  /**
   * Close the database connection.
   */
  abstract close(): Promise<void>;
}
