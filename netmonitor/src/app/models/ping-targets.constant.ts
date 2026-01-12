/**
 * Ping target options for the monitoring configuration dropdown.
 * These targets are whitelisted in the Rust backend for security.
 */

/**
 * Option for ping target dropdown selector.
 */
export interface PingTargetOption {
  /** Display label shown to user */
  label: string;
  /** Actual value used for pinging (IP or domain) */
  value: string;
}

/**
 * Pre-defined ping target options for the dropdown.
 * All values must match the ALLOWED_TARGETS whitelist in lib.rs.
 */
export const PING_TARGET_OPTIONS: PingTargetOption[] = [
  { label: 'Google DNS (8.8.8.8)', value: '8.8.8.8' },
  { label: 'Cloudflare DNS (1.1.1.1)', value: '1.1.1.1' },
  { label: 'Quad9 DNS (9.9.9.9)', value: '9.9.9.9' },
  { label: 'OpenDNS (208.67.222.222)', value: '208.67.222.222' },
  { label: 'Google Web', value: 'www.google.com' },
  { label: 'Cloudflare Web', value: 'www.cloudflare.com' }
];
