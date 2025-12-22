import { inject, Injectable } from '@angular/core';
import { DatabaseService } from './database.service';

/**
 * Repository service for persisting settings to the SQLite database.
 * Handles all database operations related to application settings.
 *
 * Settings are stored as key-value pairs where values are JSON-encoded.
 * Database keys use snake_case (e.g., 'monitoring_config').
 */
@Injectable({
  providedIn: 'root'
})
export class SettingsRepository {
  private readonly db = inject(DatabaseService);

  /**
   * Retrieve a single setting by key.
   * @param key The setting key (snake_case, e.g., 'monitoring_config')
   * @returns The parsed setting value, or null if not found or DB not initialized
   */
  async getSetting<T>(key: string): Promise<T | null> {
    if (!this.db.isInitialized) {
      return null;
    }

    try {
      const rows = await this.db.select<{ value: string }>(
        'SELECT value FROM settings WHERE key = ?',
        [key]
      );
      if (rows.length === 0) {
        return null;
      }
      return JSON.parse(rows[0].value) as T;
    } catch (err) {
      console.error(`SettingsRepository: Failed to get setting '${key}':`, err);
      return null;
    }
  }

  /**
   * Store or update a setting.
   * @param key The setting key (snake_case, e.g., 'monitoring_config')
   * @param value The value to store (will be JSON-stringified)
   */
  async setSetting<T>(key: string, value: T): Promise<void> {
    if (!this.db.isInitialized) {
      return;
    }

    try {
      await this.db.execute(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        [key, JSON.stringify(value)]
      );
    } catch (err) {
      console.error(`SettingsRepository: Failed to set setting '${key}':`, err);
    }
  }

  /**
   * Retrieve all settings as a key-value object.
   * @returns Object with all settings, or empty object if DB not initialized
   */
  async getAllSettings(): Promise<Record<string, unknown>> {
    if (!this.db.isInitialized) {
      return {};
    }

    try {
      const rows = await this.db.select<{ key: string; value: string }>(
        'SELECT key, value FROM settings'
      );

      const result: Record<string, unknown> = {};
      for (const row of rows) {
        try {
          result[row.key] = JSON.parse(row.value);
        } catch {
          // Skip malformed JSON values
          console.warn(`SettingsRepository: Skipping malformed setting '${row.key}'`);
        }
      }
      return result;
    } catch (err) {
      console.error('SettingsRepository: Failed to get all settings:', err);
      return {};
    }
  }
}
