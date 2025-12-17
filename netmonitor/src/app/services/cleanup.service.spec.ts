import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { CleanupService } from './cleanup.service';
import { PingRepository } from './ping.repository';

describe('CleanupService', () => {
  let service: CleanupService;
  let mockPingRepository: {
    deleteOldPings: ReturnType<typeof vi.fn>;
  };
  let consoleLogSpy: ReturnType<typeof vi.spyOn>;
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mockPingRepository = {
      deleteOldPings: vi.fn().mockResolvedValue(42),
    };

    TestBed.configureTestingModule({
      providers: [
        CleanupService,
        { provide: PingRepository, useValue: mockPingRepository }
      ]
    });
    service = TestBed.inject(CleanupService);

    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call pingRepository.deleteOldPings()', async () => {
    await service.runCleanup();

    expect(mockPingRepository.deleteOldPings).toHaveBeenCalled();
  });

  it('should log start message', async () => {
    await service.runCleanup();

    expect(consoleLogSpy).toHaveBeenCalledWith('CleanupService: Starting data retention cleanup...');
  });

  it('should log completion message', async () => {
    await service.runCleanup();

    expect(consoleLogSpy).toHaveBeenCalledWith('CleanupService: Cleanup complete');
  });

  it('should handle errors gracefully without throwing', async () => {
    const error = new Error('Cleanup failed');
    mockPingRepository.deleteOldPings.mockRejectedValue(error);

    await expect(service.runCleanup()).resolves.toBeUndefined();

    expect(consoleErrorSpy).toHaveBeenCalledWith('CleanupService: Cleanup failed:', error);
  });
});
