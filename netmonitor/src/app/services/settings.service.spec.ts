import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { SettingsService } from './settings.service';
import { SettingsRepository } from './settings.repository';
import { DEFAULT_SETTINGS, AppSettings, MonitoringConfig } from '../models/settings.interface';

describe('SettingsService', () => {
  let service: SettingsService;
  let mockRepository: {
    getAllSettings: ReturnType<typeof vi.fn>;
    setSetting: ReturnType<typeof vi.fn>;
    getSetting: ReturnType<typeof vi.fn>;
  };
  let consoleLogSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mockRepository = {
      getAllSettings: vi.fn().mockResolvedValue({}),
      setSetting: vi.fn().mockResolvedValue(undefined),
      getSetting: vi.fn().mockResolvedValue(null)
    };

    TestBed.configureTestingModule({
      providers: [
        SettingsService,
        { provide: SettingsRepository, useValue: mockRepository }
      ]
    });
    service = TestBed.inject(SettingsService);

    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
  });

  describe('initial state', () => {
    it('should emit DEFAULT_SETTINGS initially', async () => {
      const { firstValueFrom } = await import('rxjs');
      const settings = await firstValueFrom(service.settings$);
      expect(settings).toEqual(DEFAULT_SETTINGS);
    });

    it('should return DEFAULT_SETTINGS from getCurrentSettings()', () => {
      const settings = service.getCurrentSettings();
      expect(settings).toEqual(DEFAULT_SETTINGS);
    });
  });

  describe('loadSettings', () => {
    it('should merge loaded settings with defaults', async () => {
      const storedSettings = {
        monitoring_config: { pingTarget: '1.1.1.1', pingInterval: 10 },
        region: { countryCode: 'US', countryName: 'United States' }
      };
      mockRepository.getAllSettings.mockResolvedValue(storedSettings);

      await service.loadSettings();

      const current = service.getCurrentSettings();
      expect(current.monitoringConfig.pingTarget).toBe('1.1.1.1');
      expect(current.monitoringConfig.pingInterval).toBe(10);
      expect(current.region.countryCode).toBe('US');
      expect(current.region.countryName).toBe('United States');
      // Defaults should still apply for non-loaded fields
      expect(current.region.regulatoryBody).toBe(DEFAULT_SETTINGS.region.regulatoryBody);
    });

    it('should update settings$ observable after loading', async () => {
      const storedSettings = {
        monitoring_config: { pingTarget: '8.8.4.4' }
      };
      mockRepository.getAllSettings.mockResolvedValue(storedSettings);

      let emittedSettings: AppSettings | undefined;
      service.settings$.subscribe(s => emittedSettings = s);

      await service.loadSettings();

      expect(emittedSettings?.monitoringConfig.pingTarget).toBe('8.8.4.4');
    });

    it('should log after loading settings', async () => {
      await service.loadSettings();

      expect(consoleLogSpy).toHaveBeenCalledWith('SettingsService: Settings loaded');
    });

    it('should use defaults when no settings stored', async () => {
      mockRepository.getAllSettings.mockResolvedValue({});

      await service.loadSettings();

      const current = service.getCurrentSettings();
      expect(current).toEqual(DEFAULT_SETTINGS);
    });

    it('should handle partial stored settings', async () => {
      // Only monitoring_config stored, others should use defaults
      mockRepository.getAllSettings.mockResolvedValue({
        monitoring_config: { pingTarget: '1.0.0.1' }
        // pingInterval not stored, should use default
      });

      await service.loadSettings();

      const current = service.getCurrentSettings();
      expect(current.monitoringConfig.pingTarget).toBe('1.0.0.1');
      expect(current.monitoringConfig.pingInterval).toBe(DEFAULT_SETTINGS.monitoringConfig.pingInterval);
    });
  });

  describe('updateMonitoringConfig', () => {
    it('should persist to repository and update observable', async () => {
      const newConfig: Partial<MonitoringConfig> = { pingTarget: '1.1.1.1' };

      await service.updateMonitoringConfig(newConfig);

      expect(mockRepository.setSetting).toHaveBeenCalledWith(
        'monitoring_config',
        { ...DEFAULT_SETTINGS.monitoringConfig, pingTarget: '1.1.1.1' }
      );
    });

    it('should merge with current config preserving unchanged fields', async () => {
      // First update interval
      await service.updateMonitoringConfig({ pingInterval: 10 });
      // Then update target
      await service.updateMonitoringConfig({ pingTarget: '1.1.1.1' });

      const current = service.getCurrentSettings();
      expect(current.monitoringConfig.pingInterval).toBe(10);
      expect(current.monitoringConfig.pingTarget).toBe('1.1.1.1');
    });

    it('should emit new settings via settings$ observable', async () => {
      const emissions: AppSettings[] = [];
      service.settings$.subscribe(s => emissions.push(s));

      await service.updateMonitoringConfig({ pingTarget: 'new.target.com' });

      expect(emissions.length).toBeGreaterThan(1);
      expect(emissions[emissions.length - 1].monitoringConfig.pingTarget).toBe('new.target.com');
    });
  });

  describe('updateRegion', () => {
    it('should persist to repository', async () => {
      await service.updateRegion({ countryCode: 'US' });

      expect(mockRepository.setSetting).toHaveBeenCalledWith(
        'region',
        expect.objectContaining({ countryCode: 'US' })
      );
    });

    it('should update settings observable', async () => {
      await service.updateRegion({ countryCode: 'MX', countryName: 'Mexico' });

      const current = service.getCurrentSettings();
      expect(current.region.countryCode).toBe('MX');
      expect(current.region.countryName).toBe('Mexico');
    });
  });

  describe('updateUserInfo', () => {
    it('should persist to repository', async () => {
      await service.updateUserInfo({ name: 'John Doe', phone: '555-1234' });

      expect(mockRepository.setSetting).toHaveBeenCalledWith(
        'user_info',
        expect.objectContaining({ name: 'John Doe', phone: '555-1234' })
      );
    });

    it('should update settings observable', async () => {
      await service.updateUserInfo({ name: 'Jane Doe' });

      const current = service.getCurrentSettings();
      expect(current.userInfo.name).toBe('Jane Doe');
    });
  });

  describe('updateConnectionInfo', () => {
    it('should persist to repository', async () => {
      await service.updateConnectionInfo({
        providerName: 'ISP Corp',
        contractedSpeed: 100
      });

      expect(mockRepository.setSetting).toHaveBeenCalledWith(
        'connection_info',
        expect.objectContaining({
          providerName: 'ISP Corp',
          contractedSpeed: 100
        })
      );
    });

    it('should update settings observable', async () => {
      await service.updateConnectionInfo({ planName: 'Premium Plan' });

      const current = service.getCurrentSettings();
      expect(current.connectionInfo.planName).toBe('Premium Plan');
    });
  });

  describe('getCurrentSettings', () => {
    it('should return current settings synchronously', () => {
      const settings = service.getCurrentSettings();

      expect(settings).toBeDefined();
      expect(settings.monitoringConfig).toBeDefined();
      expect(settings.region).toBeDefined();
      expect(settings.userInfo).toBeDefined();
      expect(settings.connectionInfo).toBeDefined();
    });

    it('should reflect latest updates', async () => {
      await service.updateMonitoringConfig({ pingTarget: 'updated.com' });

      const settings = service.getCurrentSettings();

      expect(settings.monitoringConfig.pingTarget).toBe('updated.com');
    });
  });
});
