import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.pixeloddity.netmonitor',
  appName: 'NetMonitor',
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
