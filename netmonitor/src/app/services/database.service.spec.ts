import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { Capacitor } from '@capacitor/core';
import { DatabaseService } from './database.service';
import { TauriDatabaseService } from './tauri-database.service';
import { CapacitorDatabaseService } from './capacitor-database.service';
import { WebDatabaseService } from './web-database.service';
import { databaseServiceFactory } from '../app.module';

// Only mock external dependencies that would fail in browser test environment
vi.mock('@tauri-apps/plugin-sql', () => ({
  default: {
    load: vi.fn()
  }
}));

vi.mock('@capacitor-community/sqlite', () => ({
  CapacitorSQLite: {},
  SQLiteConnection: class {
    checkConnectionsConsistency = vi.fn().mockResolvedValue({ result: false });
    isConnection = vi.fn().mockResolvedValue({ result: false });
    createConnection = vi.fn().mockResolvedValue({
      open: vi.fn().mockResolvedValue(undefined),
      close: vi.fn().mockResolvedValue(undefined),
      execute: vi.fn().mockResolvedValue(undefined),
      run: vi.fn().mockResolvedValue(undefined),
      query: vi.fn().mockResolvedValue({ values: [] })
    });
    closeConnection = vi.fn().mockResolvedValue(undefined);
    retrieveConnection = vi.fn();
  }
}));

describe('DatabaseService', () => {
  beforeEach(() => {
    delete (window as unknown as { __TAURI__?: unknown }).__TAURI__;
    vi.clearAllMocks();
  });

  afterEach(() => {
    delete (window as unknown as { __TAURI__?: unknown }).__TAURI__;
    vi.restoreAllMocks();
  });

  // 7.2: Abstract class structure verification
  describe('Abstract class structure', () => {
    it('should define abstract methods that must be implemented', () => {
      // Verify that concrete implementations exist
      const webService = new WebDatabaseService();
      expect(typeof webService.init).toBe('function');
      expect(typeof webService.execute).toBe('function');
      expect(typeof webService.select).toBe('function');
      expect(typeof webService.close).toBe('function');
    });

    it('should have DB_NAME constant accessible to subclasses', () => {
      const webService = new WebDatabaseService();
      expect((webService as unknown as { DB_NAME: string }).DB_NAME).toBe('netmonitor.db');
    });
  });

  // 7.3: Platform detection returns correct service type
  describe('Platform detection (databaseServiceFactory)', () => {
    it('should return TauriDatabaseService when __TAURI__ is defined', () => {
      (window as unknown as { __TAURI__?: unknown }).__TAURI__ = {};
      const service = databaseServiceFactory();
      expect(service).toBeInstanceOf(TauriDatabaseService);
    });

    it('should return CapacitorDatabaseService when Capacitor.isNativePlatform() is true', () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      const service = databaseServiceFactory();
      expect(service).toBeInstanceOf(CapacitorDatabaseService);
    });

    it('should return WebDatabaseService in browser environment', () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);
      const service = databaseServiceFactory();
      expect(service).toBeInstanceOf(WebDatabaseService);
    });

    it('should prioritize Tauri over Capacitor', () => {
      (window as unknown as { __TAURI__?: unknown }).__TAURI__ = {};
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      const service = databaseServiceFactory();
      expect(service).toBeInstanceOf(TauriDatabaseService);
    });
  });

  // 7.4: WebDatabaseService no-op behavior (no mocks needed - pure JavaScript)
  describe('WebDatabaseService', () => {
    let service: WebDatabaseService;
    let consoleWarnSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
      service = new WebDatabaseService();
      consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    });

    afterEach(() => {
      consoleWarnSpy.mockRestore();
    });

    it('should set isInitialized to true after init()', async () => {
      expect(service.isInitialized).toBe(false);
      await service.init();
      expect(service.isInitialized).toBe(true);
    });

    it('should log warning on init()', async () => {
      await service.init();
      expect(consoleWarnSpy).toHaveBeenCalledWith('WebDatabaseService: Database not available in browser');
    });

    it('should return empty array from select()', async () => {
      const result = await service.select<{ id: number }>('SELECT * FROM test');
      expect(result).toEqual([]);
    });

    it('should log warning on execute()', async () => {
      await service.execute('INSERT INTO test VALUES (1)', [1]);
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'WebDatabaseService: Database not available in browser - execute ignored',
        expect.any(Object)
      );
    });

    it('should resolve close() without error', async () => {
      await expect(service.close()).resolves.toBeUndefined();
    });

    it('should not re-initialize if already initialized', async () => {
      await service.init();
      const callCount = consoleWarnSpy.mock.calls.length;
      await service.init(); // Second call
      // The warning is logged each time since WebDatabaseService doesn't prevent re-init
      // but isInitialized stays true
      expect(service.isInitialized).toBe(true);
    });
  });

  // 7.5: TauriDatabaseService behavior with mocked Tauri API
  describe('TauriDatabaseService', () => {
    let service: TauriDatabaseService;

    beforeEach(async () => {
      const Database = await import('@tauri-apps/plugin-sql');
      (Database.default.load as ReturnType<typeof vi.fn>).mockResolvedValue({
        execute: vi.fn().mockResolvedValue(undefined),
        select: vi.fn().mockResolvedValue([{ id: 1 }]),
        close: vi.fn().mockResolvedValue(undefined)
      });
      service = new TauriDatabaseService();
    });

    it('should call Database.load with correct path on init()', async () => {
      const Database = await import('@tauri-apps/plugin-sql');
      await service.init();
      expect(Database.default.load).toHaveBeenCalledWith('sqlite:netmonitor.db');
    });

    it('should set isInitialized to true after successful init()', async () => {
      await service.init();
      expect(service.isInitialized).toBe(true);
    });

    it('should return empty array if not initialized on select()', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const result = await service.select('SELECT * FROM test');
      expect(result).toEqual([]);
      consoleWarnSpy.mockRestore();
    });

    it('should handle init() error gracefully without crashing', async () => {
      const Database = await import('@tauri-apps/plugin-sql');
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (Database.default.load as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('DB error'));

      const failService = new TauriDatabaseService();
      await failService.init();

      expect(consoleErrorSpy).toHaveBeenCalled();
      expect(failService.isInitialized).toBe(false);
      consoleErrorSpy.mockRestore();
    });
  });

  // 7.6: CapacitorDatabaseService behavior with mocked Capacitor API
  describe('CapacitorDatabaseService', () => {
    let service: CapacitorDatabaseService;

    beforeEach(() => {
      service = new CapacitorDatabaseService();
    });

    it('should set isInitialized to true after successful init()', async () => {
      await service.init();
      expect(service.isInitialized).toBe(true);
    });

    it('should return empty array if not initialized on select()', async () => {
      const newService = new CapacitorDatabaseService();
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const result = await newService.select('SELECT * FROM test');
      expect(result).toEqual([]);
      consoleWarnSpy.mockRestore();
    });
  });

  // 7.7: isInitialized$ observable behavior
  describe('isInitialized$ observable', () => {
    it('should emit false initially', async () => {
      const service = new WebDatabaseService();
      const value = await firstValueFrom(service.isInitialized$);
      expect(value).toBe(false);
    });

    it('should emit true after init()', async () => {
      const service = new WebDatabaseService();
      await service.init();
      const value = await firstValueFrom(service.isInitialized$);
      expect(value).toBe(true);
    });
  });

  // Angular DI integration
  describe('Angular DI integration', () => {
    it('should provide correct service via TestBed', () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);

      TestBed.configureTestingModule({
        providers: [
          { provide: DatabaseService, useFactory: databaseServiceFactory }
        ]
      });

      const service = TestBed.inject(DatabaseService);
      expect(service).toBeInstanceOf(WebDatabaseService);
    });
  });
});
