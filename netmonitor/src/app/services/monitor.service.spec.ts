import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { MockedObject } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { MonitorService } from './monitor.service';
import { TauriService } from './tauri.service';
import { Capacitor } from '@capacitor/core';
import { firstValueFrom } from 'rxjs';

describe('MonitorService', () => {
  let service: MonitorService;
  let tauriServiceSpy: MockedObject<TauriService>;

  beforeEach(() => {
    vi.useFakeTimers();

    const spy = {
      invoke: vi.fn().mockName('TauriService.invoke')
    };

    TestBed.configureTestingModule({
      providers: [
        MonitorService,
        { provide: TauriService, useValue: spy }
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
});
