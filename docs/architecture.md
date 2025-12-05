# NetMonitor Brownfield Architecture Document

## Introduction
This document captures the CURRENT STATE of the NetMonitor codebase, including technical debt, workarounds, and real-world patterns, specifically focusing on the desktop application layer's transition from Electron to Tauri. It serves as a reference for AI agents working on this enhancement.

### Document Scope
Focused on areas relevant to: "Tauri Migration & Electron Removal" as detailed in `docs/prd.md`.

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 04/12/2025 | 1.0 | Initial brownfield analysis for Electron to Tauri migration | Winston (Architect) |
| 04/12/2025 | 1.1 | Updated for Tauri v2 plugin architecture & security | Winston (Architect) |
| 04/12/2025 | 1.2 | Format correction (removed header numbering) | Winston (Architect) |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System
- **Main Entry (Angular)**: `netmonitor/src/main.ts` (Angular bootstrap)
- **Main Entry (Electron)**: `netmonitor/electron/main.js` (Electron's main process, to be removed)
- **Configuration (Angular)**: `netmonitor/angular.json`, `netmonitor/tsconfig.json`
- **Configuration (Electron)**: `netmonitor/electron/main.js` (contains Electron window config), `netmonitor/package.json` (`"build"` section)
- **Core Business Logic (Angular)**: `netmonitor/src/app/` (components, services, modules)
- **Build Scripts**: `netmonitor/package.json` (`"scripts"`), `netmonitor/angular.json`
- **Capacitor Configuration**: `netmonitor/capacitor.config.ts`, `netmonitor/ionic.config.json`

### Enhancement Impact Areas
- `netmonitor/electron/`: This entire directory and its contents will be removed.
- `netmonitor/package.json`: Dependencies (`electron`, `electron-builder`) will be removed; build scripts will be updated; a new `tauri:dev` script will be added.
- `netmonitor/src/`: The Angular frontend will remain largely unchanged, but its build output (`www` or `dist` folder) will be consumed by Tauri.
- Project root: A new `src-tauri/` directory will be created, containing Tauri's configuration (`tauri.conf.json`) and Rust backend code.

## High Level Architecture

### Technical Summary
The NetMonitor application currently utilizes an Ionic/Angular frontend, packaged with Capacitor for Android, and Electron for desktop builds. The desktop build is monolithic, bundling Chromium and Node.js. The proposed change involves replacing Electron with Tauri, which leverages native webviews and a Rust backend, drastically reducing the desktop binary footprint.

### Actual Tech Stack (Current State)

| Category | Technology | Version | Notes |
| :--- | :--- | :--- | :--- |
| Frontend Framework | Angular | ~21 | Used across all platforms (Web, Android, Desktop) |
| UI Framework | Ionic | ~8 | Provides UI components for cross-platform consistency |
| Mobile Container | Capacitor | ~7 | Used for Android builds |
| Desktop Container | Electron | ~39 | **Target for removal/replacement** (bloated desktop build) |
| Desktop Builder | electron-builder | ~26 | **Target for removal/replacement** |
| Languages | TypeScript, JavaScript | | For frontend and Electron main process |
| Package Manager | npm/yarn | | (Based on `package-lock.json`) |

### Repository Structure Reality Check
- Type: Hybrid (Monorepo-like for app, separate mobile/desktop build tools)
- Package Manager: npm (implied by `package-lock.json`)
- Notable: Contains `src/` for Angular, `electron/` for desktop, `android/` for mobile. `node_modules` are shared.

## Source Tree and Module Organization

### Project Structure (Actual - before Tauri)

```text
NetMonitor/
├── netmonitor/ # Main application directory
│   ├── .angular/
│   ├── .vscode/
│   ├── android/        # Capacitor Android project (remains)
│   │   └── ...
│   ├── electron/       # Electron main process and config (to be removed)
│   │   ├── main.js     # Electron entry point
│   │   └── ...
│   ├── node_modules/
│   ├── src/            # Angular source code (remains)
│   │   ├── app/        # Angular components, services, modules
│   │   ├── assets/
│   │   └── ...
│   ├── www/            # Angular build output (consumed by Electron, then by Tauri)
│   ├── angular.json    # Angular workspace configuration
│   ├── package.json    # Project dependencies and scripts
│   └── tsconfig.json
├── docs/               # Project documentation
│   ├── prd.md          # Product Requirements Document
│   └── RELATORIO_MIGRACAO_TAURI.md # Migration Report
├── .bmad-core/         # Agent's internal files
├── .git/
└── README.md
```

### Key Modules and Their Purpose
- **Angular Frontend (`netmonitor/src/app/`)**: Contains all the application's user interface, business logic, and services, designed to run in a web environment.
- **Electron Main Process (`netmonitor/electron/main.js`)**: Manages the Electron window, IPC, and native desktop interactions. **This entire module will be superseded by Tauri's native layer.**
- **Capacitor Android Project (`netmonitor/android/`)**: Standard Android project generated by Capacitor, responsible for packaging the web content into an Android app. **Unaffected by the migration.**

## Data Models and APIs
- **Frontend Communication**: The Angular frontend communicates via standard HTTP/HTTPS requests, not through Electron's IPC (which will be removed). Tauri will also expose a standard webview for the frontend.
- **Related Types**: TypeScript interfaces/classes within `netmonitor/src/app/models/`.

## Technical Debt and Known Issues
- **Desktop Build Bloat**: The primary technical debt being addressed is the large footprint of the Electron desktop application.
- **Electron-specific configurations**: Existing Electron configurations in `package.json` (`"build"` section) and `electron/main.js` represent debt that ties the project to Electron.

## Integration Points and External Dependencies

### External Services
- **HTTP Latency Monitoring**: Frontend makes HTTP requests to external services for latency checks. This remains unchanged.

### Internal Integration Points
- **Frontend-to-Container**: The Angular frontend's compiled output (`www` directory) is currently served by Electron. In the new architecture, it will be served by Tauri.
- **Native OS Features**: Electron provides access to native OS features; Tauri will provide similar access via its Rust backend and plugin system.
- **Angular Configuration**: `angular.json` may require specific headers (e.g., `Cross-Origin-Opener-Policy`) to function correctly within Tauri's isolated security context.

## Development and Deployment

### Local Development Setup
- `ng serve`: Starts the Angular development server (remains unchanged).
- `npm run electron:start`: Builds Angular and runs Electron (to be replaced by Tauri's dev workflow).

### Build and Deployment Process
- **Current Desktop Build**: `npm run build && electron-builder` (or similar) is used for Electron desktop packages.
- **New Desktop Build**: `ng build` (for Angular) followed by `cargo tauri build` will be the new process.
- **Android Build**: `ionic cap run android` (remains unchanged).

## Enhancement PRD Provided - Impact Analysis

### Files That Will Need Modification
- `netmonitor/package.json`: Removal of Electron dependencies and build scripts, addition of Tauri-related scripts.
- `netmonitor/angular.json`: Configuration for output directory and potentially `serve.options.headers` for security context.

### New Files/Modules Needed
- `netmonitor/src-tauri/`: This new directory will house all Tauri-specific files:
    - `src-tauri/Cargo.toml`: Rust project configuration (Must define dependencies for Tauri Plugins like `tauri-plugin-shell`).
    - `src-tauri/src/main.rs`: Tauri's Rust backend entry point.
    - `src-tauri/tauri.conf.json`: Tauri's application configuration.
    - `src-tauri/capabilities/`: Security configuration for Tauri v2 permissions.

### Integration Considerations
- Frontend routing must be compatible with a file-based serving approach (relative paths).
- Any native system calls must use Tauri Plugins (v2 architecture) rather than direct API calls.
- `angular.json` should be checked for `architect.serve.options.headers` if strict isolation is needed.

## Appendix - Useful Commands and Scripts

### Frequently Used Commands
- `ng serve`: Start Angular development server.
- `ionic cap run android`: Build and run Android application.
- `npm install`: Install dependencies.

### New Commands (post-Tauri migration)
- `npx tauri dev`: Start Tauri development server with live reload.
- `npx tauri build`: Build Tauri production application.
