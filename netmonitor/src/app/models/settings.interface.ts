/**
 * Settings interfaces for NetMonitor application.
 * These types define the structure of all configurable settings
 * that are persisted to SQLite and exposed via SettingsService.
 */

/**
 * Monitoring configuration settings.
 * Controls ping target and polling interval.
 */
export interface MonitoringConfig {
  /** Target host/URL to ping (e.g., '8.8.8.8', 'https://google.com') */
  pingTarget: string;
  /** Polling interval in seconds */
  pingInterval: number;
}

/**
 * Region configuration for regulatory compliance reporting.
 * Used in complaint generation and export features.
 */
export interface RegionConfig {
  /** ISO 3166-1 alpha-2 country code (e.g., 'BR', 'US') */
  countryCode: string;
  /** Full country name (e.g., 'Brasil', 'United States') */
  countryName: string;
  /** Telecommunications regulatory body (e.g., 'Anatel', 'FCC') */
  regulatoryBody: string;
  /** Consumer protection agency (e.g., 'PROCON', 'FTC') */
  consumerProtection: string;
  /** Applicable telecommunications law reference */
  applicableLaw: string;
}

/**
 * User information for complaint generation.
 * All fields are optional to allow incremental data entry.
 */
export interface UserInfo {
  /** User's full name */
  name: string;
  /** Document number (CPF, SSN, etc.) */
  document: string;
  /** Type of document (e.g., 'CPF', 'CNPJ', 'SSN') */
  documentType: string;
  /** Full address */
  address: string;
  /** Phone number */
  phone: string;
  /** Optional geolocation coordinates */
  geolocation?: {
    latitude: number;
    longitude: number;
  };
}

/**
 * Internet connection information for complaint generation.
 * Contains ISP and contract details.
 */
export interface ConnectionInfo {
  /** Internet Service Provider name */
  providerName: string;
  /** Contracted plan name */
  planName: string;
  /** Contracted speed in Mbps (null if not set) */
  contractedSpeed: number | null;
  /** Connection type (e.g., 'fiber', 'cable', 'dsl', 'mobile') */
  connectionType: string | null;
  /** Contract or account number */
  contractNumber: string;
}

/**
 * Complete application settings combining all configuration sections.
 */
export interface AppSettings {
  /** Monitoring/ping configuration */
  monitoringConfig: MonitoringConfig;
  /** Regional settings for compliance */
  region: RegionConfig;
  /** User identification info */
  userInfo: UserInfo;
  /** ISP connection details */
  connectionInfo: ConnectionInfo;
}

/**
 * Default settings values used when no persisted settings exist.
 * These values are applied on first app launch or when settings are reset.
 */
export const DEFAULT_SETTINGS: AppSettings = {
  monitoringConfig: {
    pingTarget: '8.8.8.8',  // Google DNS
    pingInterval: 5         // 5 seconds
  },
  region: {
    countryCode: 'BR',
    countryName: 'Brasil',
    regulatoryBody: 'Anatel',
    consumerProtection: 'PROCON',
    applicableLaw: 'Marco Civil da Internet'
  },
  userInfo: {
    name: '',
    document: '',
    documentType: 'CPF',
    address: '',
    phone: ''
  },
  connectionInfo: {
    providerName: '',
    planName: '',
    contractedSpeed: null,
    connectionType: null,
    contractNumber: ''
  }
};
