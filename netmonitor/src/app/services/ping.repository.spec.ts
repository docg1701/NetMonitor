import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { PingRepository } from './ping.repository';
import { DatabaseService } from './database.service';
import { PingResult } from '../models/ping-result.interface';

describe('PingRepository', () => {
  let repository: PingRepository;
  let mockDb: {
    execute: ReturnType<typeof vi.fn>;
    isInitialized: boolean;
  };

  beforeEach(() => {
    mockDb = {
      isInitialized: true,
      execute: vi.fn().mockResolvedValue(undefined),
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
