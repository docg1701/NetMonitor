# NetMonitor Enterprise

NetMonitor is a modern, cross-platform network latency monitoring tool designed to be stable, permission-friendly, and easy to use. It provides real-time visualization and statistics for network performance monitoring.

This application is a complete modernization of a legacy Python tool, rewritten using Angular, Ionic, Capacitor, and Electron (soon to be Tauri) to ensure native performance and stability on Linux, Windows, and Android.

## Features

*   **Real-Time Monitoring:** Uses efficient HTTP HEAD requests to measure latency without requiring Root/Administrator permissions or ICMP access.
*   **Visual Dashboard:** Interactive line chart visualizing latency history (last 50 points).
*   **Live Statistics:** Instant updates for Current Latency, Average, Minimum, Maximum, and Jitter.
*   **Dark Mode:** Designed with a sleek, dark-themed interface for comfortable long-term monitoring.
*   **Cross-Platform:**
    *   **Desktop:** Runs as a native application on Linux and Windows.
    *   **Mobile:** Runs as a native Android application.
*   **Status Indicator:** Clear Online/Offline visual status.

## Tech Stack

*   **Frontend:** Angular v21+
*   **UI Framework:** Ionic Framework v8+
*   **Runtime (Desktop):** Electron v39+ (Migration to Tauri planned for size optimization)
*   **Runtime (Mobile):** Capacitor v7+
*   **Charts:** Chart.js with ng2-charts

## Installation & Usage

### Linux (AppImage)
1.  Download the latest `.AppImage` from the releases page (or build it locally).
2.  Make it executable: `chmod +x NetMonitor-x.x.x.AppImage`
3.  Run it: `./NetMonitor-x.x.x.AppImage`

### Android
1.  Open the project in Android Studio (`npx cap open android`).
2.  Build and Run on your device or emulator.

## Development

### Prerequisites
*   Node.js (v20 or higher)
*   NPM (v10 or higher)
*   Ionic CLI (`npm install -g @ionic/cli`)

### Setup
```bash
cd netmonitor
npm install
```

### Running Locally (Web)
To test the UI in a browser:
```bash
npm start
# or
ionic serve
```

### Building for Desktop (Electron)
```bash
npm run build            # Builds the Angular app
npx electron-builder build --linux  # Packages for Linux
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
