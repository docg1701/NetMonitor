import { inject, Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { SettingsRepository } from './settings.repository';
import {
  AppSettings,
  MonitoringConfig,
  RegionConfig,
  UserInfo,
  ConnectionInfo,
  DEFAULT_SETTINGS
} from '../models/settings.interface';

/** Database key for monitoring configuration */
const KEY_MONITORING_CONFIG = 'monitoring_config';
/** Database key for region settings */
const KEY_REGION = 'region';
/** Database key for user information */
const KEY_USER_INFO = 'user_info';
/** Database key for connection information */
const KEY_CONNECTION_INFO = 'connection_info';

/**
 * Service for managing application settings.
 * Provides reactive access to settings via Observable and handles persistence.
 *
 * Usage:
 * - Subscribe to `settings$` for reactive updates
 * - Use `getCurrentSettings()` for synchronous access
 * - Call `loadSettings()` during app initialization
 * - Use update methods to modify and persist settings
 */
@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private readonly settingsRepository = inject(SettingsRepository);

  /** Private BehaviorSubject for internal state management */
  private readonly _settings$ = new BehaviorSubject<AppSettings>(DEFAULT_SETTINGS);

  /** Public Observable for consumers to subscribe to settings changes */
  readonly settings$: Observable<AppSettings> = this._settings$.asObservable();

  /**
   * Load settings from database and merge with defaults.
   * Should be called during app initialization (APP_INITIALIZER).
   * Missing settings will use default values.
   */
  async loadSettings(): Promise<void> {
    const stored = await this.settingsRepository.getAllSettings();

    const merged: AppSettings = {
      monitoringConfig: {
        ...DEFAULT_SETTINGS.monitoringConfig,
        ...(stored[KEY_MONITORING_CONFIG] as Partial<MonitoringConfig> | undefined)
      },
      region: {
        ...DEFAULT_SETTINGS.region,
        ...(stored[KEY_REGION] as Partial<RegionConfig> | undefined)
      },
      userInfo: {
        ...DEFAULT_SETTINGS.userInfo,
        ...(stored[KEY_USER_INFO] as Partial<UserInfo> | undefined)
      },
      connectionInfo: {
        ...DEFAULT_SETTINGS.connectionInfo,
        ...(stored[KEY_CONNECTION_INFO] as Partial<ConnectionInfo> | undefined)
      }
    };

    this._settings$.next(merged);
    console.log('SettingsService: Settings loaded');
  }

  /**
   * Get current settings synchronously.
   * @returns Current AppSettings value
   */
  getCurrentSettings(): AppSettings {
    return this._settings$.getValue();
  }

  /**
   * Update monitoring configuration.
   * @param config Partial MonitoringConfig to merge with current settings
   */
  async updateMonitoringConfig(config: Partial<MonitoringConfig>): Promise<void> {
    const current = this._settings$.getValue();
    const updated: MonitoringConfig = {
      ...current.monitoringConfig,
      ...config
    };

    await this.settingsRepository.setSetting(KEY_MONITORING_CONFIG, updated);

    this._settings$.next({
      ...current,
      monitoringConfig: updated
    });
  }

  /**
   * Update region configuration.
   * @param region Partial RegionConfig to merge with current settings
   */
  async updateRegion(region: Partial<RegionConfig>): Promise<void> {
    const current = this._settings$.getValue();
    const updated: RegionConfig = {
      ...current.region,
      ...region
    };

    await this.settingsRepository.setSetting(KEY_REGION, updated);

    this._settings$.next({
      ...current,
      region: updated
    });
  }

  /**
   * Update user information.
   * @param userInfo Partial UserInfo to merge with current settings
   */
  async updateUserInfo(userInfo: Partial<UserInfo>): Promise<void> {
    const current = this._settings$.getValue();
    const updated: UserInfo = {
      ...current.userInfo,
      ...userInfo
    };

    await this.settingsRepository.setSetting(KEY_USER_INFO, updated);

    this._settings$.next({
      ...current,
      userInfo: updated
    });
  }

  /**
   * Update connection information.
   * @param connectionInfo Partial ConnectionInfo to merge with current settings
   */
  async updateConnectionInfo(connectionInfo: Partial<ConnectionInfo>): Promise<void> {
    const current = this._settings$.getValue();
    const updated: ConnectionInfo = {
      ...current.connectionInfo,
      ...connectionInfo
    };

    await this.settingsRepository.setSetting(KEY_CONNECTION_INFO, updated);

    this._settings$.next({
      ...current,
      connectionInfo: updated
    });
  }
}
