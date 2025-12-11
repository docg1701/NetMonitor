import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'io.ionic.starter',
  appName: 'netmonitor',
  webDir: 'www/browser',
  resources: {
    android: {
      icon: 'resources/icon.svg'
    },
    ios: {
      icon: 'resources/icon.svg'
    }
  }
};

export default config;
