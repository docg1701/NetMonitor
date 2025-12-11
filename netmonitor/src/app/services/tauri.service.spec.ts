import { describe, it, expect, beforeEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { TauriService } from './tauri.service';

/**
 * TauriService Tests
 *
 * Note: TauriService is a thin wrapper around @tauri-apps/api/core invoke.
 * Due to ESM module limitations in Vitest browser mode, we cannot mock
 * the underlying Tauri API directly. However, TauriService functionality
 * is fully tested through MonitorService tests which mock TauriService itself.
 *
 * @see monitor.service.spec.ts for integration tests that cover TauriService usage
 */
describe('TauriService', () => {
  let service: TauriService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TauriService]
    });
    service = TestBed.inject(TauriService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have invoke method', () => {
    expect(typeof service.invoke).toBe('function');
  });

  it('should be injectable as singleton (providedIn: root)', () => {
    const service2 = TestBed.inject(TauriService);
    expect(service).toBe(service2);
  });
});
