import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { PingRepository } from './ping.repository';
import { DatabaseService } from './database.service';
import { PingResult } from '../models/ping-result.interface';

describe('PingRepository', () => {
  let repository: PingRepository;
  let mockDb: {
    execute: ReturnType<typeof vi.fn>;
    executeWithCount: ReturnType<typeof vi.fn>;
    isInitialized: boolean;
  };

  beforeEach(() => {
    mockDb = {
      isInitialized: true,
      execute: vi.fn().mockResolvedValue(undefined),
      executeWithCount: vi.fn().mockResolvedValue(42),
    };

    TestBed.configureTestingModule({
      providers: [
        PingRepository,
        { provide: DatabaseService, useValue: mockDb }
      ]
    });
    repository = TestBed.inject(PingRepository);
  });

  it('should call execute with correct SQL and params', async () => {
    const result: PingResult = {
      timestamp: new Date('2024-01-15T10:30:00Z'),
      latencyMs: 42.5,
      status: 'ok'
    };

    await repository.savePing(result, 'https://google.com');

    expect(mockDb.execute).toHaveBeenCalledWith(
      'INSERT INTO pings (timestamp, latency_ms, success, target) VALUES (?, ?, ?, ?)',
      [1705314600000, 42.5, 1, 'https://google.com']
    );
  });

  it('should convert timestamp to Unix epoch correctly', async () => {
    const testDate = new Date('2024-06-20T15:45:30.500Z');
    const result: PingResult = {
      timestamp: testDate,
      latencyMs: 100,
      status: 'ok'
    };

    await repository.savePing(result, 'https://example.com');

    expect(mockDb.execute).toHaveBeenCalledWith(
      expect.any(String),
      expect.arrayContaining([testDate.getTime()])
    );
  });

  it('should convert success status to 1 for ok', async () => {
    const result: PingResult = {
      timestamp: new Date(),
      latencyMs: 50,
      status: 'ok'
    };

    await repository.savePing(result, 'https://test.com');

    const callArgs = mockDb.execute.mock.calls[0][1];
    expect(callArgs[2]).toBe(1);
  });

  it('should convert success status to 0 for error', async () => {
    const result: PingResult = {
      timestamp: new Date(),
      latencyMs: null,
      status: 'error'
    };

    await repository.savePing(result, 'https://test.com');

    const callArgs = mockDb.execute.mock.calls[0][1];
    expect(callArgs[2]).toBe(0);
  });

  it('should handle null latencyMs for error results', async () => {
    const result: PingResult = {
      timestamp: new Date(),
      latencyMs: null,
      status: 'error'
    };

    await repository.savePing(result, 'https://test.com');

    const callArgs = mockDb.execute.mock.calls[0][1];
    expect(callArgs[1]).toBeNull();
  });

  it('should catch and log database errors without throwing', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const dbError = new Error('Database connection failed');
    mockDb.execute.mockRejectedValue(dbError);

    const result: PingResult = {
      timestamp: new Date(),
      latencyMs: 100,
      status: 'ok'
    };

    // Should not throw
    await expect(repository.savePing(result, 'https://test.com')).resolves.toBeUndefined();

    expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to persist ping:', dbError);
    consoleErrorSpy.mockRestore();
  });

  it('should return early when database not initialized', async () => {
    mockDb.isInitialized = false;

    const result: PingResult = {
      timestamp: new Date(),
      latencyMs: 100,
      status: 'ok'
    };

    await repository.savePing(result, 'https://test.com');

    expect(mockDb.execute).not.toHaveBeenCalled();
  });
});

describe('PingRepository.deleteOldPings', () => {
  let repository: PingRepository;
  let mockDb: {
    execute: ReturnType<typeof vi.fn>;
    executeWithCount: ReturnType<typeof vi.fn>;
    isInitialized: boolean;
  };
  let consoleLogSpy: ReturnType<typeof vi.spyOn>;
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;
  let dateNowSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mockDb = {
      isInitialized: true,
      execute: vi.fn().mockResolvedValue(undefined),
      executeWithCount: vi.fn().mockResolvedValue(42),
    };

    TestBed.configureTestingModule({
      providers: [
        PingRepository,
        { provide: DatabaseService, useValue: mockDb }
      ]
    });
    repository = TestBed.inject(PingRepository);

    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    if (dateNowSpy) {
      dateNowSpy.mockRestore();
    }
  });

  it('should delete pings older than 30 days by default', async () => {
    const now = 1702800000000; // Fixed timestamp
    dateNowSpy = vi.spyOn(Date, 'now').mockReturnValue(now);

    await repository.deleteOldPings();

    const expectedCutoff = now - (30 * 24 * 60 * 60 * 1000);
    expect(mockDb.executeWithCount).toHaveBeenCalledWith(
      'DELETE FROM pings WHERE timestamp < ?',
      [expectedCutoff]
    );
  });

  it('should use custom retention period when provided', async () => {
    const now = 1702800000000;
    dateNowSpy = vi.spyOn(Date, 'now').mockReturnValue(now);

    await repository.deleteOldPings(7);

    const expectedCutoff = now - (7 * 24 * 60 * 60 * 1000);
    expect(mockDb.executeWithCount).toHaveBeenCalledWith(
      'DELETE FROM pings WHERE timestamp < ?',
      [expectedCutoff]
    );
  });

  it('should return 0 when database not initialized', async () => {
    mockDb.isInitialized = false;

    const result = await repository.deleteOldPings();

    expect(result).toBe(0);
    expect(mockDb.executeWithCount).not.toHaveBeenCalled();
  });

  it('should return count of deleted records', async () => {
    mockDb.executeWithCount.mockResolvedValue(150);

    const result = await repository.deleteOldPings();

    expect(result).toBe(150);
  });

  it('should catch errors and return 0', async () => {
    const dbError = new Error('Database error');
    mockDb.executeWithCount.mockRejectedValue(dbError);

    const result = await repository.deleteOldPings();

    expect(result).toBe(0);
    expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to delete old pings:', dbError);
  });

  it('should log deletion count', async () => {
    mockDb.executeWithCount.mockResolvedValue(42);

    await repository.deleteOldPings();

    expect(consoleLogSpy).toHaveBeenCalledWith('PingRepository: Deleted 42 old ping records');
  });
});
