# NetMonitor Brownfield Enhancement PRD

## Intro Project Analysis and Context

### Existing Project Overview
#### Analysis Source
- User-provided information (Migration Report: `docs/RELATORIO_MIGRACAO_TAURI.md`)
- IDE-based fresh analysis of `netmonitor/package.json` and project structure.

#### Current Project State
NetMonitor is a cross-platform network monitoring utility (latency via HTTP).
- **Frontend**: Angular (v21+), Ionic 8, Chart.js.
- **Desktop**: Currently uses Electron 39. Builds ~132MB AppImage on Linux.
- **Mobile**: Android version uses Capacitor 7.
- **Problem**: Electron adds excessive overhead (Chromium + Node.js) for a simple utility, resulting in large binary size and high memory usage.
- **UI State**: Currently only supports a Dark Theme.

### Documentation Analysis
#### Available Documentation
- [x] Tech Stack Documentation (Inferred from `package.json`)
- [x] Source Tree/Architecture (Standard Ionic/Angular structure verified)
- [ ] Coding Standards
- [ ] API Documentation (Not applicable, simple utility)
- [x] Migration Report (`docs/RELATORIO_MIGRACAO_TAURI.md`)

### Enhancement Scope Definition
#### Enhancement Type
- [x] New Feature Addition (Theme System)
- [ ] Major Feature Modification
- [x] Technology Stack Upgrade (Electron → Tauri)
- [x] Performance/Scalability Improvements
- [x] CI/CD & Release Management

#### Enhancement Description
1. Migrate the Desktop layer from Electron to Tauri.
2. Implement a Light/Dark theme system.
3. Establish a release pipeline to validate and publish v1.0 across Windows, Linux, macOS, and Android.

#### Impact Assessment
- [ ] Minimal Impact
- [ ] Moderate Impact
- [x] Significant Impact (Architecture + UI + CI/CD)
- [ ] Major Impact

### Goals and Background Context
#### Goals
- Reduce Desktop executable size by ~90% (target < 15MB).
- Maintain exact visual parity for the existing Dark Theme.
- Introduce a fully functional Light Theme.
- **Publish verified v1.0 release artifacts for all major platforms on GitHub.**

#### Background Context
The application is evolving from a heavy Electron prototype to a polished, multi-platform production app. Validating the build process and successfully publishing artifacts for all target OSs is critical to mark the v1.0 milestone.

#### Change Log
| Change | Date | Version | Description | Author |
| :--- | :--- | :--- | :--- | :--- |
| Initial PRD Draft | 04/12/2025 | 1.0 | Migration to Tauri | PM Agent |
| v2 Update | 04/12/2025 | 1.1 | Added Tauri v2 Plugin & Capabilities | Architect Agent |
| v3 Update | 04/12/2025 | 1.2 | Added Light/Dark Theme Requirements | PM Agent |
| v4 Update | 04/12/2025 | 1.3 | Added Multi-platform Release Epic | PM Agent |
| v5 Update | 04/12/2025 | 1.4 | Format correction (removed header numbering) | PM Agent |
| v6 Update | 04/12/2025 | 1.5 | Addressed PO Recommendations (Docs & Charts) | PM Agent |

## Requirements

### Functional
- FR1: The system must compile the existing Angular frontend into a Tauri-compatible desktop application.
- FR2: The `electron-builder` dependency and configuration must be completely removed.
- FR3: The application must use `src-tauri` for the backend configuration.
- FR4: The application must launch on Linux using WebKitGTK.
- FR5: The application must support two distinct visual themes: Light and Dark.
- FR6: The UI must include a toggle button to change the active theme.
- FR7: The selected theme must be persisted.
- **FR8**: The CI/CD pipeline (or manual release process) must generate valid installable artifacts for Windows (.msi/.exe), Linux (.AppImage/.deb), macOS (.app/.dmg), and Android (.apk).
- **FR9**: All artifacts must be published to a GitHub Release tagged `v1.0.0`.

### Non Functional
- NFR1: The final Linux AppImage/Deb must be < 20MB.
- NFR2: Theme switching must occur immediately without page reload.
- **NFR4**: macOS builds must be signed (or notarized if possible, otherwise explicitly documented as unsigned).
- **NFR5**: Android release must be a signed APK or App Bundle suitable for sideloading or Play Store.

### Compatibility Requirements
- CR1: API Compatibility: Frontend must operate without Electron IPC.
- CR2: Android Compatibility: Mobile build must also support the new theming system.
- CR3: Developer Experience: `ng serve` must support theme testing.

## User Interface Enhancement Goals
### Integration with Existing UI
- The new Light Theme must use the same layout and components as the existing Dark Theme.
- The Theme Toggle button should be placed unobtrusively.

### UI Consistency Requirements
- Color palettes for Light Mode must ensure sufficient contrast ratio (WCAG AA).
- **Chart Readability**: Chart.js components must adapt their colors (grid lines, tooltips, data points) to ensure readability in both Light and Dark modes.

## Technical Constraints and Integration Requirements

### Existing Technology Stack
- **Languages**: TypeScript, HTML, SCSS, Rust
- **Frameworks**: Angular 21, Ionic 8, Capacitor 7, Tauri 2.x
- **Infrastructure**: Linux, Android, GitHub Actions (Proposed)

### Integration Approach
- **Release Automation**: Use `tauri-action` for desktop builds and standard Capacitor build commands for Android.

### Risk Assessment
- **Cross-Platform Build Risk**: Building macOS/Windows artifacts typically requires running on those OSs (GitHub Actions runners are needed).
- **Signing Certificates**: macOS and Windows usually require paid certificates to avoid security warnings. *Mitigation: Accept unsigned builds for v1.0 or use self-signed/Open Source licenses if applicable.*
- **Chart Visualization Risk**: Charts may be illegible in Light Mode if using fixed dark colors. *Mitigation: Implement dynamic styling logic for Chart.js instances.*

## Epic and Story Structure

### Epic Approach
**Epic Structure Decision**: The work will be divided into **three distinct epics**.
1.  **Epic 1: Tauri Migration** (Technical Foundation)
2.  **Epic 2: Theme System** (UI Enhancement)
3.  **Epic 3: Multi-Platform Validation & Release** (Delivery)

### Epic 1: Tauri Migration & Electron Removal
**Epic Goal**: Migrate from Electron to Tauri.

#### Story 1: Environment Preparation & Tauri Initialization
As a **Developer**, I want to **prepare the development environment for Tauri and initialize its project structure**, so that **I can begin integrating the Angular frontend into the new desktop framework.**
##### Acceptance Criteria
1: Rust toolchain and Tauri CLI are installed.
2: `npx tauri init` is successfully run, creating the `src-tauri` directory.
3: The `src-tauri` directory contains a minimal, compilable Tauri project.
4: Essential Tauri v2 plugins (if any) are identified and added to `Cargo.toml`.
##### Integration Verification
IV1: The existing `ng serve` command still functions correctly.
IV2: A simple `cargo build --target=x86_64-unknown-linux-gnu` (or appropriate host target) within `src-tauri` completes without errors.

#### Story 2: Development Workflow Integration & Frontend Configuration
As a **Developer**, I want to **configure Tauri to serve the Angular application during development and integrate it into the existing `package.json` scripts**, so that **I can seamlessly develop the frontend with live-reloading and test within the Tauri environment.**
##### Acceptance Criteria
1: `src-tauri/tauri.conf.json` is configured to point to the Angular `www` (or build output) directory (configured as `frontendDist`).
2: `package.json` contains a new script (e.g., `tauri:dev`) that starts `ng serve` and `tauri dev` concurrently.
3: `angular.json` is updated with necessary headers (e.g., Cross-Origin) if required for specific Tauri features.
4: The Angular application is correctly displayed in the Tauri window during `tauri dev`.
##### Integration Verification
IV1: Changes in Angular code are reflected live in the Tauri dev window.
IV2: Frontend routes and API calls (e.g., `HttpClient`) function as expected within Tauri.

#### Story 3: Electron Removal & Project Cleanup
As a **Developer**, I want to **remove all Electron-related dependencies and files from the project**, so that **the project is clean, lean, and solely uses Tauri for desktop builds.**
##### Acceptance Criteria
1: `electron` and `electron-builder` packages are uninstalled from `package.json`.
2: The `electron/` directory is deleted.
3: `package.json` scripts related to Electron (e.g., `electron:start`) are removed.
4: The `main` field in `package.json` referencing `electron/main.js` is removed or updated.
##### Integration Verification
IV1: The project still builds and runs correctly with Tauri.
IV2: `git status` shows no lingering Electron files or configuration.

#### Story 4: Production Build Configuration & Verification
As a **Developer**, I want to **configure Tauri for production builds and verify the final application artifact**, so that **I can confirm the successful migration and deliver a small, performant desktop application.**
##### Acceptance Criteria
1: `tauri.conf.json` contains necessary production settings (app name, icon, bundle ID).
2: `src-tauri/capabilities/` is configured with appropriate permissions for the production release.
3: `cargo tauri build` successfully generates a release artifact (e.g., `.AppImage` for Linux).
4: The size of the generated artifact is within the target (e.g., < 20MB).
##### Integration Verification
IV1: The installed release application functions identically to the previous Electron version regarding UI and core features.
IV2: System resource monitoring confirms reduced memory footprint compared to Electron.

### Epic 2: Theme System Implementation
**Epic Goal**: Implement a robust Light/Dark theme system with user control.

#### Story 5: CSS Variable Refactoring
As a **Developer**, I want to **refactor existing hardcoded colors into CSS variables (or ensure Ionic variables are used)**, so that **I can easily invert the color scheme for Light Mode.**
##### Acceptance Criteria
1: All structural colors (backgrounds, text, borders) use CSS variables.
2: A `light-theme` (or default) and `dark-theme` class structure is defined in `global.scss`.
3: The application looks identical to the current version when the Dark theme is active.

#### Story 6: Theme Toggle & Persistence
As a **User**, I want to **click a button to switch themes and have the app remember my choice**, so that **I can customize the viewing experience.**
##### Acceptance Criteria
1: A clickable button/icon (Sun/Moon) is added to the UI header.
2: Clicking the button instantly toggles between Light and Dark modes.
3: The user's preference is saved to `localStorage` (or Ionic Storage).
4: On app launch, the saved preference is loaded; if none, OS preference is used.
5: **Chart.js visualizations are validated to be legible in both Light and Dark modes (e.g., dynamic grid/label colors).**

### Epic 3: Multi-Platform Validation & Release v1.0
**Epic Goal**: configure CI/CD and build processes to successfully generate and publish v1.0 installers for Windows, Linux, macOS, and Android on GitHub.

#### Story 7: GitHub Actions CI/CD Configuration (Desktop)
As a **DevOps Engineer**, I want to **configure a GitHub Action workflow that builds Tauri apps for Windows, Linux, and macOS**, so that **I can automatically generate cross-platform artifacts.**
##### Acceptance Criteria
1: A `.github/workflows/release.yml` file is created.
2: The workflow triggers on `v*` tags.
3: The workflow successfully builds:
   - Linux (`ubuntu-latest`): AppImage, Deb
   - Windows (`windows-latest`): MSI or NSIS .exe
   - macOS (`macos-latest`): DMG or App
4: Artifacts are uploaded to the GitHub Release.
5: **A brief `RELEASE_PROCESS.md` (or section in README) is created documenting how to trigger and manage these releases.**
##### Integration Verification
IV1: Pushing a `v1.0.0` tag triggers the action.
IV2: The action completes all jobs green.

#### Story 8: Android Release Build Pipeline
As a **Mobile Developer**, I want to **generate a signed Android APK/AAB**, so that **I can publish the mobile version alongside the desktop versions.**
##### Acceptance Criteria
1: The build process generates a signed release APK.
2: The Android build is integrated into the GitHub Release workflow (or documented manual upload).
3: The APK installs and runs on a physical Android device.

#### Story 9: v1.0 Final Verification
As a **QA Specialist**, I want to **install and run the generated artifacts on each platform**, so that **I can validate the application works as expected before public announcement.**
##### Acceptance Criteria
1: Windows .exe installs and launches correctly; Theme toggle works.
2: Linux AppImage runs; Tauri backend functions.
3: macOS .app runs (checking for quarantine/signing issues).
4: Android APK installs; network monitoring functions.