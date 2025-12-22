import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { SettingsRepository } from './settings.repository';
import { DatabaseService } from './database.service';

describe('SettingsRepository', () => {
  let repository: SettingsRepository;
  let mockDb: {
    execute: ReturnType<typeof vi.fn>;
    select: ReturnType<typeof vi.fn>;
    isInitialized: boolean;
  };
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;
  let consoleWarnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mockDb = {
      isInitialized: true,
      execute: vi.fn().mockResolvedValue(undefined),
      select: vi.fn().mockResolvedValue([]),
    };

    TestBed.configureTestingModule({
      providers: [
        SettingsRepository,
        { provide: DatabaseService, useValue: mockDb }
      ]
    });
    repository = TestBed.inject(SettingsRepository);

    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });

  describe('getSetting', () => {
    it('should return null when database not initialized', async () => {
      mockDb.isInitialized = false;

      const result = await repository.getSetting('test_key');

      expect(result).toBeNull();
      expect(mockDb.select).not.toHaveBeenCalled();
    });

    it('should return parsed JSON value when setting exists', async () => {
      const storedValue = { pingTarget: '8.8.8.8', pingInterval: 5 };
      mockDb.select.mockResolvedValue([{ value: JSON.stringify(storedValue) }]);

      const result = await repository.getSetting<typeof storedValue>('monitoring_config');

      expect(result).toEqual(storedValue);
      expect(mockDb.select).toHaveBeenCalledWith(
        'SELECT value FROM settings WHERE key = ?',
        ['monitoring_config']
      );
    });

    it('should return null when setting does not exist', async () => {
      mockDb.select.mockResolvedValue([]);

      const result = await repository.getSetting('non_existent_key');

      expect(result).toBeNull();
    });

    it('should handle database errors gracefully and return null', async () => {
      const dbError = new Error('Database connection failed');
      mockDb.select.mockRejectedValue(dbError);

      const result = await repository.getSetting('test_key');

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "SettingsRepository: Failed to get setting 'test_key':",
        dbError
      );
    });
  });

  describe('setSetting', () => {
    it('should return early when database not initialized', async () => {
      mockDb.isInitialized = false;

      await repository.setSetting('test_key', { value: 'test' });

      expect(mockDb.execute).not.toHaveBeenCalled();
    });

    it('should call execute with correct SQL and JSON-stringified value', async () => {
      const value = { pingTarget: '1.1.1.1', pingInterval: 10 };

      await repository.setSetting('monitoring_config', value);

      expect(mockDb.execute).toHaveBeenCalledWith(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        ['monitoring_config', JSON.stringify(value)]
      );
    });

    it('should handle string values correctly', async () => {
      await repository.setSetting('simple_key', 'simple_value');

      expect(mockDb.execute).toHaveBeenCalledWith(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        ['simple_key', '"simple_value"']
      );
    });

    it('should handle number values correctly', async () => {
      await repository.setSetting('retention_days', 30);

      expect(mockDb.execute).toHaveBeenCalledWith(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        ['retention_days', '30']
      );
    });

    it('should handle database errors gracefully without throwing', async () => {
      const dbError = new Error('Write failed');
      mockDb.execute.mockRejectedValue(dbError);

      await expect(repository.setSetting('test_key', 'value')).resolves.toBeUndefined();

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "SettingsRepository: Failed to set setting 'test_key':",
        dbError
      );
    });
  });

  describe('getAllSettings', () => {
    it('should return empty object when database not initialized', async () => {
      mockDb.isInitialized = false;

      const result = await repository.getAllSettings();

      expect(result).toEqual({});
      expect(mockDb.select).not.toHaveBeenCalled();
    });

    it('should return key-value object of all settings', async () => {
      mockDb.select.mockResolvedValue([
        { key: 'monitoring_config', value: '{"pingTarget":"8.8.8.8","pingInterval":5}' },
        { key: 'region', value: '{"countryCode":"BR","countryName":"Brasil"}' },
        { key: 'retention_days', value: '30' }
      ]);

      const result = await repository.getAllSettings();

      expect(result).toEqual({
        monitoring_config: { pingTarget: '8.8.8.8', pingInterval: 5 },
        region: { countryCode: 'BR', countryName: 'Brasil' },
        retention_days: 30
      });
      expect(mockDb.select).toHaveBeenCalledWith('SELECT key, value FROM settings');
    });

    it('should skip malformed JSON values with warning', async () => {
      mockDb.select.mockResolvedValue([
        { key: 'valid_key', value: '{"valid":"json"}' },
        { key: 'invalid_key', value: 'not valid json {' },
        { key: 'another_valid', value: '"string value"' }
      ]);

      const result = await repository.getAllSettings();

      expect(result).toEqual({
        valid_key: { valid: 'json' },
        another_valid: 'string value'
      });
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "SettingsRepository: Skipping malformed setting 'invalid_key'"
      );
    });

    it('should handle database errors gracefully and return empty object', async () => {
      const dbError = new Error('Select failed');
      mockDb.select.mockRejectedValue(dbError);

      const result = await repository.getAllSettings();

      expect(result).toEqual({});
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'SettingsRepository: Failed to get all settings:',
        dbError
      );
    });
  });
});
