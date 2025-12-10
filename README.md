# NetMonitor Enterprise

![Latest Release](https://img.shields.io/github/v/release/docg1701/NetMonitor)

NetMonitor is a modern, cross-platform network latency monitoring tool designed to be stable, permission-friendly, and easy to use. It provides real-time visualization and statistics for network performance monitoring.

This application is rewritten using Angular, Ionic, Capacitor, and Tauri to ensure native performance and stability on Linux, Windows, macOS, and Android.

## Features

*   **Real-Time Monitoring:** Uses native Rust commands (Desktop) or efficient HTTP HEAD requests (Mobile) to measure latency.
*   **Visual Dashboard:** Interactive line chart visualizing latency history (last 50 points).
*   **Live Statistics:** Instant updates for Current Latency, Average, Minimum, Maximum, and Jitter.
*   **Dark Mode:** Designed with a sleek, dark-themed interface for comfortable long-term monitoring.
*   **Cross-Platform:**
    *   **Desktop:** Runs as a native application on Linux, Windows, and macOS (via Tauri).
    *   **Mobile:** Runs as a native Android application (via Capacitor).
*   **Status Indicator:** Clear Online/Offline visual status.

## Tech Stack

*   **Frontend:** Angular v21+
*   **UI Framework:** Ionic Framework v8+
*   **Runtime (Desktop):** Tauri v2 (Rust backend)
*   **Runtime (Mobile):** Capacitor v7+
*   **Charts:** Chart.js with ng2-charts

## Installation & Usage

### Desktop (Linux/Windows/macOS)
1.  Download the latest installer/bundle from the [Releases Page](../../releases/latest).
2.  Install/Run according to your OS (AppImage, .exe/msi, .dmg).

### Android
1.  Download the latest `.apk` from the Releases page.
2.  Install on your device.

## Development

### Prerequisites
*   Node.js (v20 or higher)
*   Rust (latest stable)
*   Ionic CLI (`npm install -g @ionic/cli`)
*   Tauri CLI (`npm install -g @tauri-apps/cli`)

### Setup
```bash
cd netmonitor
npm install
```

### Running Locally
To test the UI in a browser:
```bash
npm start
```
To run the Desktop app in development mode:
```bash
npm run tauri:dev
```

### Building for Desktop (Tauri)
```bash
npm run tauri build
```

### Building for Android
```bash
npm run build
npx cap sync
npx cap open android
```

### Release Process
See [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) for instructions on creating and publishing new releases.

## License
[MIT License](LICENSE)
