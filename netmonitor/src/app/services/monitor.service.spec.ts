import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { MockedObject } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { MonitorService } from './monitor.service';
import { TauriService } from './tauri.service';
import { PingRepository } from './ping.repository';
import { SettingsService } from './settings.service';
import { DEFAULT_SETTINGS, AppSettings } from '../models/settings.interface';
import { Capacitor } from '@capacitor/core';
import { BehaviorSubject, firstValueFrom } from 'rxjs';

describe('MonitorService', () => {
  let service: MonitorService;
  let tauriServiceSpy: MockedObject<TauriService>;
  let pingRepositorySpy: { savePing: ReturnType<typeof vi.fn> };
  let settingsServiceSpy: {
    getCurrentSettings: ReturnType<typeof vi.fn>;
    settings$: BehaviorSubject<AppSettings>;
  };

  beforeEach(() => {
    vi.useFakeTimers();

    const spy = {
      invoke: vi.fn().mockName('TauriService.invoke')
    };

    pingRepositorySpy = {
      savePing: vi.fn().mockResolvedValue(undefined)
    };

    settingsServiceSpy = {
      getCurrentSettings: vi.fn().mockReturnValue(DEFAULT_SETTINGS),
      settings$: new BehaviorSubject<AppSettings>(DEFAULT_SETTINGS)
    };

    TestBed.configureTestingModule({
      providers: [
        MonitorService,
        { provide: TauriService, useValue: spy },
        { provide: PingRepository, useValue: pingRepositorySpy },
        { provide: SettingsService, useValue: settingsServiceSpy }
      ]
    });
    service = TestBed.inject(MonitorService);
    tauriServiceSpy = TestBed.inject(TauriService) as MockedObject<TauriService>;

    // Clear any Tauri mock from previous tests
    delete (window as any).__TAURI__;
  });

  afterEach(() => {
    service.stopMonitoring();
    vi.useRealTimers();
    vi.restoreAllMocks();
    delete (window as any).__TAURI__;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // RT-001: Should emit ping results via results$ observable
  describe('RT-001: results$ observable', () => {
    it('should emit ping results via results$ observable', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 42 });

      service.startMonitoring(1000);

      // Advance timer and flush promises
      await vi.advanceTimersByTimeAsync(100);

      const results = await firstValueFrom(service.results$);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].status).toBe('ok');
      expect(results[0].latencyMs).toBe(42);
    });
  });

  // RT-002: Should maintain maximum 50 results in history
  describe('RT-002: 50 results history limit', () => {
    it('should maintain maximum 50 results in history', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 10 });

      service.startMonitoring(10);

      // Generate 60 results
      for (let i = 0; i < 60; i++) {
        await vi.advanceTimersByTimeAsync(10);
      }

      const results = await firstValueFrom(service.results$);
      expect(results.length).toBeLessThanOrEqual(50);
    });
  });

  // RT-003: Should correctly detect Tauri platform
  describe('RT-003: Tauri platform detection', () => {
    it('should correctly detect Tauri platform', async () => {
      (window as any).__TAURI__ = { invoke: vi.fn() };
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 50 });

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      expect(tauriServiceSpy.invoke).toHaveBeenCalled();
    });

    it('should not use Tauri when __TAURI__ is not defined', async () => {
      delete (window as any).__TAURI__;

      // Mock fetch for web fallback
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({} as Response);
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      expect(tauriServiceSpy.invoke).not.toHaveBeenCalled();
      fetchSpy.mockRestore();
    });
  });

  // RT-004: Should correctly detect Capacitor platform
  describe('RT-004: Capacitor platform detection', () => {
    it('should use fetch on web platform', async () => {
      delete (window as any).__TAURI__;
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({} as Response);

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      expect(fetchSpy).toHaveBeenCalled();
    });
  });

  // Test for stopMonitoring() properly unsubscribes
  describe('stopMonitoring', () => {
    it('should stop polling when stopMonitoring is called', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 10 });

      service.startMonitoring(100);
      await vi.advanceTimersByTimeAsync(200);

      const callCount = tauriServiceSpy.invoke.mock.calls.length;

      service.stopMonitoring();
      await vi.advanceTimersByTimeAsync(500);

      // No new calls after stopping
      expect(tauriServiceSpy.invoke.mock.calls.length).toBe(callCount);
    });

    it('should handle multiple stopMonitoring calls gracefully', () => {
      service.stopMonitoring();
      service.stopMonitoring();
      expect(service).toBeTruthy();
    });
  });

  // Test for error status handling (null latencyMs)
  describe('error status handling', () => {
    it('should emit error result with null latencyMs on Tauri error', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockRejectedValue(new Error('Network error'));

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      const results = await firstValueFrom(service.results$);
      expect(results.length).toBeGreaterThan(0);

      const lastResult = results[results.length - 1];
      expect(lastResult.status).toBe('error');
      expect(lastResult.latencyMs).toBeNull();
    });

    it('should emit error result with null latencyMs on web fetch error', async () => {
      delete (window as any).__TAURI__;
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);
      vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Fetch failed'));

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      const results = await firstValueFrom(service.results$);
      expect(results.length).toBeGreaterThan(0);

      const lastResult = results[results.length - 1];
      expect(lastResult.status).toBe('error');
      expect(lastResult.latencyMs).toBeNull();
    });
  });

  // Test for ok status handling (valid latencyMs)
  describe('ok status handling', () => {
    it('should emit ok result with valid latencyMs from Tauri', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 123 });

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      const results = await firstValueFrom(service.results$);
      expect(results.length).toBeGreaterThan(0);

      const lastResult = results[results.length - 1];
      expect(lastResult.status).toBe('ok');
      expect(lastResult.latencyMs).toBe(123);
      expect(lastResult.timestamp).toBeInstanceOf(Date);
    });
  });

  // Persistence integration tests (Story 1.3)
  describe('persistence integration', () => {
    it('should emit results via results$ regardless of database state', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 42 });
      // Simulate database error
      pingRepositorySpy.savePing.mockRejectedValue(new Error('DB error'));

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      const results = await firstValueFrom(service.results$);
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].latencyMs).toBe(42);
    });

    it('should call savePing after each ping result', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 50 });

      service.startMonitoring(100);
      await vi.advanceTimersByTimeAsync(350);

      // Should have at least 3 calls (initial + 2 intervals)
      expect(pingRepositorySpy.savePing.mock.calls.length).toBeGreaterThanOrEqual(3);
    });

    it('should call savePing with correct ping result and target', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 75 });

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      expect(pingRepositorySpy.savePing).toHaveBeenCalled();
      const [result, target] = pingRepositorySpy.savePing.mock.calls[0];
      expect(result.latencyMs).toBe(75);
      expect(result.status).toBe('ok');
      expect(result.timestamp).toBeInstanceOf(Date);
      expect(target).toBe('8.8.8.8');
    });

    it('should continue monitoring when database errors occur', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 30 });
      pingRepositorySpy.savePing.mockRejectedValue(new Error('Database failure'));

      service.startMonitoring(100);

      // Let multiple pings occur
      await vi.advanceTimersByTimeAsync(350);

      const results = await firstValueFrom(service.results$);
      // Should have multiple results despite DB errors
      expect(results.length).toBeGreaterThanOrEqual(3);
    });

    it('should not block ping timing due to database write', async () => {
      (window as any).__TAURI__ = true;
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 20 });

      // Simulate slow database write
      pingRepositorySpy.savePing.mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 500))
      );

      service.startMonitoring(100);
      await vi.advanceTimersByTimeAsync(350);

      // Should have multiple results even though DB is slow
      const results = await firstValueFrom(service.results$);
      expect(results.length).toBeGreaterThanOrEqual(3);
    });
  });

  // Settings integration tests (Story 2.1)
  describe('settings integration', () => {
    it('should use ping target from settings when available', async () => {
      (window as any).__TAURI__ = true;
      const customSettings: AppSettings = {
        ...DEFAULT_SETTINGS,
        monitoringConfig: {
          pingTarget: 'custom.server.com',
          pingInterval: 10
        }
      };
      settingsServiceSpy.getCurrentSettings.mockReturnValue(customSettings);
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 50 });

      service.startMonitoring(1000);
      await vi.advanceTimersByTimeAsync(100);

      // Verify Tauri invoke was called with the custom target
      expect(tauriServiceSpy.invoke).toHaveBeenCalledWith('ping', { url: 'custom.server.com' });

      // Verify savePing was called with the custom target
      expect(pingRepositorySpy.savePing).toHaveBeenCalled();
      const [, target] = pingRepositorySpy.savePing.mock.calls[0];
      expect(target).toBe('custom.server.com');
    });

    it('should use ping interval from settings when no override provided', async () => {
      (window as any).__TAURI__ = true;
      const customSettings: AppSettings = {
        ...DEFAULT_SETTINGS,
        monitoringConfig: {
          pingTarget: '8.8.8.8',
          pingInterval: 2  // 2 seconds = 2000ms
        }
      };
      settingsServiceSpy.getCurrentSettings.mockReturnValue(customSettings);
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 25 });

      // Start monitoring without providing interval (should use settings)
      service.startMonitoring();

      // Advance by 2500ms - should have 2 calls (initial + 1 interval at 2000ms)
      await vi.advanceTimersByTimeAsync(2500);

      const results = await firstValueFrom(service.results$);
      // Should have exactly 2 results with 2000ms interval in 2500ms
      expect(results.length).toBe(2);
    });

    it('should override settings interval when custom interval provided', async () => {
      (window as any).__TAURI__ = true;
      const customSettings: AppSettings = {
        ...DEFAULT_SETTINGS,
        monitoringConfig: {
          pingTarget: '8.8.8.8',
          pingInterval: 10  // 10 seconds = 10000ms from settings
        }
      };
      settingsServiceSpy.getCurrentSettings.mockReturnValue(customSettings);
      tauriServiceSpy.invoke.mockResolvedValue({ latency_ms: 30 });

      // Start monitoring with custom 500ms interval (overrides settings 10s)
      service.startMonitoring(500);

      // Advance by 1200ms - should have 3 calls with 500ms interval
      await vi.advanceTimersByTimeAsync(1200);

      const results = await firstValueFrom(service.results$);
      // Should have 3 results (0ms, 500ms, 1000ms) despite settings saying 10s
      expect(results.length).toBe(3);
    });
  });
});
