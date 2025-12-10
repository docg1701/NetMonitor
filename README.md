# NetMonitor

<p align="center">
  <img src="icon.svg" alt="NetMonitor Icon" width="128" height="128">
</p>

![Latest Release](https://img.shields.io/github/v/release/docg1701/NetMonitor?label=latest%20release)

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

*   **Frontend:** Angular v21.0.0
*   **UI Framework:** Ionic Framework v8.0.0
*   **Runtime (Desktop):** Tauri v2.9.4 (Rust backend)
*   **Runtime (Mobile):** Capacitor v7.4.4
*   **Charts:** Chart.js v4.5.1 with ng2-charts v8.0.0
*   **Rust Dependencies:** reqwest v0.12, serde v1.0, tauri-plugin-log/shell/store v2

## Installation & Usage

### Desktop (Linux/Windows/macOS)
1.  Download the latest installer/bundle from the [Releases Page](../../releases/latest).
2.  Install/Run according to your OS (AppImage, .exe/msi, .dmg).

**Linux Helper Script:**
After building the AppImage or downloading it from Releases, use `install_linux.sh` to add NetMonitor to your system menu.

**What the script does:**
*   Copies the AppImage to `~/.local/bin/`
*   Extracts the application icon from the AppImage
*   Creates a `.desktop` file in `~/.local/share/applications/`
*   The app will appear in your menu under the "Internet" category

**Installation:**
```bash
chmod +x install_linux.sh
./install_linux.sh netmonitor/src-tauri/target/release/bundle/appimage/NetMonitor_1.0.4_amd64.AppImage
```

**Uninstallation:**
```bash
./install_linux.sh --uninstall
```

This works on Linux Mint, Ubuntu, and other distributions using XDG desktop standards.

### Android
1.  Download the latest `.apk` from the Releases page.
2.  Install on your device.

## Development

### Prerequisites
*   Node.js v20 or higher
*   Rust v1.77.2 or higher (latest stable recommended)
*   Ionic CLI (`npm install -g @ionic/cli`)
*   Tauri CLI (`npm install -g @tauri-apps/cli`)
*   mold linker (optional, for faster builds)

### System Dependencies

#### Linux (Ubuntu/Debian/Mint)
```bash
sudo apt update
sudo apt install -y \
  build-essential \
  libgtk-3-dev \
  libwebkit2gtk-4.1-dev \
  libjavascriptcoregtk-4.1-dev \
  libsoup-3.0-dev \
  librsvg2-dev \
  patchelf \
  pkg-config \
  mold

# For system tray support (Ubuntu/Debian/Mint):
sudo apt install -y libayatana-appindicator3-dev
```

> **Note:** The project is configured to use the `mold` linker for faster Rust compilation. If you don't install mold, remove the `rustflags` line from `netmonitor/.cargo/config.toml`.

#### Installing Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
rustc --version  # Verify installation
```

#### Android Build Requirements
*   JDK 17 (required by Gradle)
*   Android SDK with API level 35
*   Set environment variables:
```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

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

### Building for Desktop (Linux AppImage)

**Complete step-by-step:**

1.  Install system dependencies (see above)
2.  Install Rust (see above)
3.  Install Node.js v20+ (via nvm or package manager)
4.  Install global CLI tools:
    ```bash
    npm install -g @ionic/cli @tauri-apps/cli
    ```
5.  Install project dependencies:
    ```bash
    cd netmonitor
    npm install
    ```
6.  Build the application:
    ```bash
    npm run tauri build
    ```
7.  The AppImage will be generated at:
    ```
    src-tauri/target/release/bundle/appimage/NetMonitor_X.X.X_amd64.AppImage
    ```

### Building for Android (via Command Line)

1.  Install project dependencies:
    ```bash
    cd netmonitor
    npm install
    ```
2.  Build the Angular frontend:
    ```bash
    npm run build
    ```
3.  Sync with Capacitor:
    ```bash
    npx cap sync android
    ```
4.  Build the APK (debug):
    ```bash
    cd android
    ./gradlew assembleDebug
    ```
    The APK will be at: `android/app/build/outputs/apk/debug/app-debug.apk`

5.  Build the APK (release - requires signing):
    ```bash
    ./gradlew assembleRelease
    ```

### Release Process
See [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) for instructions on creating and publishing new releases.

## License
[MIT License](LICENSE)
