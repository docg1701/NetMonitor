# NetMonitor Brownfield Architecture Document

## Introduction

This document captures the **CURRENT STATE** of the NetMonitor codebase, including technical constraints, patterns, and workarounds. It serves as a reference for AI agents working on the Post-MVP enhancement (SQLite persistence, Settings tab, Reports tab, AdMob monetization).

### Document Scope

**Focused on areas relevant to:** Post-MVP Enhancement as defined in `docs/prd.md`
- SQLite persistence layer integration
- Tab-based navigation restructuring
- Settings and Reports tab implementation
- AdMob integration (mobile only)

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-10 | 1.0 | Initial brownfield analysis | Architect Agent |

---

## Compatibility Requirements

### CR1: Existing API Compatibility

The `MonitorService` interface SHALL remain unchanged to avoid breaking the Monitor tab.

**Protected Methods:**
- `startMonitoring(intervalMs)` - begin real-time ping measurement
- `stopMonitoring()` - pause real-time ping measurement
- `results$` - Observable stream of PingResult objects

**Implementation Impact:** Internal modifications allowed (add persistence layer), but public interface must remain unchanged. Regression test suite (Story 1.0) verifies these methods continue working identically.

### CR2: Database Schema Compatibility

Initial schema SHALL support forward migration using versioned migrations from day one.

**Migration Strategy:**
- Each schema version numbered sequentially (v1, v2, etc.)
- Migrations idempotent (safe to run multiple times)
- Migration system tracks schema version in database
- Future schema changes applied safely without data loss

### CR3: UI/UX Consistency

New tabs SHALL follow existing Ionic component patterns and dark/light theme support.

**Required Patterns:**
- All components MUST respect `ion-palette-dark` toggle
- Use only Ionic 8 components: `ion-card`, `ion-item`, `ion-input`, `ion-select`, `ion-button`, `ion-list`, `ion-accordion`
- Ionicons for all icons (already imported)
- Forms: `ion-item` + `ion-input`/`ion-select` pattern
- Feedback: `ion-toast` for success/error, `ion-alert` for confirmations

### CR4: Platform Parity

Core functionality SHALL work identically on Desktop (Tauri) and Mobile (Capacitor), with ads being the only mobile-specific feature.

| Feature | Desktop (Tauri) | Mobile (Capacitor) |
|---------|-----------------|-------------------|
| SQLite persistence | tauri-plugin-sql | @capacitor-community/sqlite |
| Settings management | Identical | Identical |
| Reports & export | Identical | Identical |
| Banner ads | None | @capacitor-community/admob |
| Rewarded ads | None | @capacitor-community/admob |
| Geolocation | navigator.geolocation | @capacitor/geolocation |

---

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

| Purpose | File Path | Notes |
|---------|-----------|-------|
| **Angular Entry** | `netmonitor/src/main.ts` | Bootstraps AppModule |
| **App Module** | `netmonitor/src/app/app.module.ts` | NgModule-based (NOT standalone) |
| **App Component** | `netmonitor/src/app/app.component.ts` | Root component, `standalone: false` |
| **App Routing** | `netmonitor/src/app/app-routing.module.ts` | Single route to home |
| **Monitor Page** | `netmonitor/src/app/home/home.page.ts` | Main UI, standalone component |
| **Monitor Service** | `netmonitor/src/app/services/monitor.service.ts` | Core ping logic |
| **Tauri Service** | `netmonitor/src/app/services/tauri.service.ts` | Tauri IPC wrapper |
| **Tauri Backend** | `netmonitor/src-tauri/src/lib.rs` | Rust ping command |
| **Tauri Config** | `netmonitor/src-tauri/tauri.conf.json` | App metadata, window config |
| **Capacitor Config** | `netmonitor/capacitor.config.ts` | Mobile app config |
| **Theme Variables** | `netmonitor/src/theme/variables.scss` | CSS custom properties |
| **Environment** | `netmonitor/src/environments/environment.ts` | Runtime config |

### Enhancement Impact Areas

Based on the PRD, these areas will be modified or created:

**Files to Modify:**
- `app.component.html` - Add `ion-tabs` wrapper
- `app-routing.module.ts` - Convert to tab-based routing
- `monitor.service.ts` - Add database persistence calls
- `AndroidManifest.xml` - Add AdMob, geolocation permissions
- `Cargo.toml` - Add `tauri-plugin-sql`
- `lib.rs` - Register SQL plugin, possibly modify ping target handling

**New Files Needed:**
- `src/app/tabs/` - Tab container component
- `src/app/settings/` - Settings page
- `src/app/reports/` - Reports page
- `src/app/services/database.service.ts` - SQLite abstraction
- `src/app/services/settings.service.ts` - Settings management
- `src/app/services/export.service.ts` - JSON/prompt export
- `src/app/services/ip.service.ts` - Public IP lookup
- `src/app/services/ad.service.ts` - AdMob wrapper (mobile)
- `src/app/models/settings.interface.ts` - Settings data model

---

## High Level Architecture

### Technical Summary

NetMonitor is a **cross-platform network latency monitoring tool** built with:
- **Frontend:** Angular 21 + Ionic 8 (hybrid approach: NgModule root + standalone pages)
- **Desktop Runtime:** Tauri 2.9.x (Rust backend)
- **Mobile Runtime:** Capacitor 7.4.x (native Android/iOS bridges)
- **State Management:** RxJS BehaviorSubject pattern (no NgRx/Redux)

### Tech Stack (Complete Reference)

#### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Angular | 21.0.0 | Application framework |
| Ionic | 8.0.0 | UI component library |
| TypeScript | 5.9.x | Language |
| RxJS | 7.8.x | Reactive programming |
| Chart.js | 4.5.1 | Data visualization |
| ng2-charts | 8.0.0 | Angular Chart.js wrapper |

#### Desktop Runtime (Tauri)

| Technology | Version | Purpose |
|------------|---------|---------|
| Tauri | 2.9.4 | Desktop app framework |
| Rust | 1.77.2+ | Backend language |
| reqwest | 0.12 | HTTP client (5s timeout) |
| serde | 1.0 | Serialization |
| tauri-plugin-log | 2.x | Logging |
| tauri-plugin-shell | 2.x | Shell commands |
| tauri-plugin-store | 2.x | Key-value storage |

#### Mobile Runtime (Capacitor)

| Technology | Version | Purpose |
|------------|---------|---------|
| Capacitor | 7.4.4 | Mobile app framework |
| @capacitor/android | 7.4.4 | Android runtime |
| @capacitor/ios | 7.4.4 | iOS runtime |
| @capacitor/app | 7.1.1 | App lifecycle |
| @capacitor/haptics | 7.0.3 | Haptic feedback |
| @capacitor/keyboard | 7.0.4 | Keyboard handling |
| @capacitor/status-bar | 7.0.4 | Status bar control |

#### Build Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| Angular CLI | 21.0.0 | Build orchestration |
| Tauri CLI | 2.9.5 | Desktop builds |
| Capacitor CLI | 7.4.4 | Mobile builds |
| ESLint | 9.16.x | Code linting |
| Vitest | 3.x | Test framework & runner |
| Playwright | 1.x | Browser test provider |

#### Planned Additions (Post-MVP)

| Technology | Version | Purpose |
|------------|---------|---------|
| tauri-plugin-sql | 2.x | SQLite for desktop |
| @capacitor-community/sqlite | 7.x | SQLite for mobile |
| @capacitor/geolocation | 7.x | GPS coordinates |
| @capacitor-community/admob | 6.x | Mobile ads |

---

## Data Models and Schema

### Database Tables

#### pings (primary monitoring data)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| timestamp | INTEGER | Unix timestamp (indexed for query performance) |
| latency_ms | REAL | Latency in milliseconds (nullable for errors) |
| success | INTEGER | 1 = ok, 0 = error |
| target | TEXT | Ping destination address |

**Index:** `CREATE INDEX idx_pings_timestamp ON pings(timestamp)`

#### settings (application configuration)

| Column | Type | Description |
|--------|------|-------------|
| key | TEXT | Primary key, setting identifier |
| value | TEXT | JSON-encoded setting value |

**Example keys:** `ping_target`, `ping_interval`, `region`, `user_info`, `connection_info`, `retention_days`

#### outages (network interruption tracking)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| start_time | INTEGER | Unix timestamp of outage start |
| end_time | INTEGER | Unix timestamp of outage end (nullable if ongoing) |
| duration_ms | INTEGER | Calculated duration in milliseconds |
| ip_before | TEXT | Public IP at outage start (optional) |
| ip_after | TEXT | Public IP at outage end (optional) |

### Schema Integration Strategy

**Migration Approach:**
- Version 1: Create `pings` and `settings` tables (Story 1.2)
- Version 2: Add `outages` table (Story 3.2)
- Each migration checks current version before applying
- Migrations are idempotent and non-destructive

**Backward Compatibility:**
- Existing app data preserved during upgrades
- Schema version tracked in settings table
- Failed migrations logged but don't crash app

---

### Repository Structure Reality Check

- **Type:** Monorepo (single `netmonitor/` folder contains all platforms)
- **Package Manager:** npm (package-lock.json present)
- **Notable:**
  - Angular output goes to `www/` (Ionic convention)
  - Tauri looks for frontend in `../www` relative to `src-tauri/`
  - Android project in `android/`, iOS in `ios/`

---

## Source Tree and Module Organization

### Repository Structure

```
NetMonitor/
├── .bmad-core/              # BMAD framework configuration
├── .claude/                 # Claude Code configuration
├── docs/                    # Documentation
│   ├── references/          # Reference documents
│   │   ├── POST-MVP-ROADMAP.md
│   │   └── RELEASE_PROCESS.md
│   ├── architecture.md      # This document
│   └── prd.md              # Product Requirements Document
├── netmonitor/             # Main application source
│   ├── android/            # Capacitor Android project
│   ├── ios/                # Capacitor iOS project
│   ├── src/                # Angular source code
│   ├── src-tauri/          # Tauri/Rust backend
│   └── www/                # Build output
├── icon.svg                # App icon source
├── install_linux.sh        # Linux installer script
└── README.md               # Project overview
```

### Angular Source (`netmonitor/src/`)

```
src/
├── app/
│   ├── home/                    # Monitor page (standalone)
│   │   ├── home.page.ts         # Component + all monitor logic
│   │   ├── home.page.html       # Template with chart + stats cards
│   │   ├── home.page.scss       # Page-specific styles
│   │   ├── home.page.spec.ts    # Unit tests
│   │   └── home-routing.module.ts  # UNUSED - legacy file
│   ├── models/
│   │   └── ping-result.interface.ts  # PingResult type definition
│   ├── services/
│   │   ├── monitor.service.ts       # Core monitoring logic
│   │   ├── monitor.service.spec.ts  # Service tests
│   │   └── tauri.service.ts         # Tauri IPC wrapper
│   ├── app.component.ts         # Root component (NOT standalone)
│   ├── app.component.html       # <ion-router-outlet> only
│   ├── app.component.scss       # Empty
│   ├── app.component.spec.ts    # Smoke test
│   ├── app.module.ts            # NgModule bootstrap
│   └── app-routing.module.ts    # Route configuration
├── assets/                  # Static assets
│   ├── icon/               # PWA icons
│   └── shapes.svg          # Ionic shapes
├── environments/
│   ├── environment.ts      # Development config
│   └── environment.prod.ts # Production config
├── theme/
│   └── variables.scss      # Ionic theme + custom CSS vars
├── global.scss             # Global styles / Ionic imports
├── index.html              # SPA entry point
├── main.ts                 # Angular bootstrap
├── manifest.webmanifest    # PWA manifest
├── polyfills.ts            # Browser polyfills
├── test.ts                 # Test configuration
└── zone-flags.ts           # Zone.js flags
```

### Tauri Source (`netmonitor/src-tauri/`)

```
src-tauri/
├── capabilities/
│   └── default.json        # Tauri capabilities config
├── icons/                  # App icons (all sizes)
├── src/
│   ├── lib.rs             # Main Rust code (ping command)
│   └── main.rs            # Entry point
├── target/                # Build output (gitignored)
├── build.rs               # Build script
├── Cargo.lock             # Rust dependency lock
├── Cargo.toml             # Rust dependencies
└── tauri.conf.json        # Tauri configuration
```

### Key File Responsibilities

| File | Responsibility |
|------|----------------|
| `home.page.ts` | Chart rendering, statistics calculation, theme toggle, monitoring control |
| `monitor.service.ts` | Platform detection, ping measurement, results streaming |
| `tauri.service.ts` | Tauri IPC abstraction for invoke calls |
| `lib.rs` | Rust HTTP HEAD request for latency measurement |
| `variables.scss` | All CSS custom properties for theming |
| `environment.ts` | Runtime configuration (pingUrl) |

### Key Modules and Their Purpose

| Module | Location | Purpose | Pattern |
|--------|----------|---------|---------|
| **HomePage** | `home/home.page.ts` | All monitor UI + logic | Standalone component with `inject()` |
| **MonitorService** | `services/monitor.service.ts` | Ping measurement, results stream | BehaviorSubject, platform detection |
| **TauriService** | `services/tauri.service.ts` | Tauri IPC abstraction | Simple wrapper around `@tauri-apps/api` |
| **AppModule** | `app.module.ts` | Root NgModule | Traditional NgModule pattern |
| **AppComponent** | `app.component.ts` | App shell | `standalone: false` (legacy) |

---

## Architecture Patterns and Conventions

### Component Pattern: Hybrid Standalone/NgModule

**CRITICAL:** The project uses a **hybrid approach**:
- `AppComponent` is `standalone: false` and bootstrapped via `AppModule`
- `HomePage` is `standalone: true` and loaded via `loadComponent()`

```typescript
// app-routing.module.ts - Standalone component loading
{
  path: 'home',
  loadComponent: () => import('./home/home.page').then(m => m.HomePage)
}

// app.component.ts - NOT standalone
@Component({
  standalone: false,  // <-- Important!
})
export class AppComponent {}
```

**For new pages:** Use standalone components with `loadComponent()` to match existing pattern.

### Service Pattern: BehaviorSubject State

Services use RxJS BehaviorSubject for reactive state:

```typescript
// monitor.service.ts pattern
private _results$ = new BehaviorSubject<PingResult[]>([]);
readonly results$ = this._results$.asObservable();
```

**For new services:** Follow this pattern for reactive state management.

### Dependency Injection: Modern `inject()` Function

The HomePage uses Angular 14+ `inject()` function:

```typescript
// home.page.ts
monitorService = inject(MonitorService);
cd = inject(ChangeDetectorRef);
```

**For new components:** Use `inject()` instead of constructor injection.

### Platform Detection Pattern

```typescript
// monitor.service.ts
private isTauri(): boolean {
  return !!(window as any).__TAURI__;
}

// For Capacitor
import { Capacitor } from '@capacitor/core';
if (Capacitor.isNativePlatform()) { ... }
```

**CRITICAL:** Always check platform before using platform-specific APIs.

### Theme Pattern

Dark mode is controlled via CSS class on `<body>`:

```typescript
// home.page.ts
if (this.isDark) {
  document.body.classList.add('ion-palette-dark');
} else {
  document.body.classList.remove('ion-palette-dark');
}
```

CSS custom properties update chart colors:
```scss
// variables.scss
:root {
  --chart-line-color: #3880ff;
}
.ion-palette-dark {
  --chart-line-color: rgba(148, 159, 177, 1);
}
```

---

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Hardcoded Ping Target in Rust Backend**
   - **Location:** `src-tauri/src/lib.rs:15`
   - **Issue:** `ALLOWED_DOMAIN` is hardcoded to `www.google.com`
   - **Impact:** PRD FR3 (configurable ping target) requires Rust changes
   - **Solution:** Expand to whitelist of allowed targets (dropdown selection in UI)

   ```rust
   // Current constraint
   const ALLOWED_DOMAIN: &str = "www.google.com";

   // Will be changed to whitelist:
   const ALLOWED_TARGETS: &[&str] = &[
       "8.8.8.8",           // Google DNS
       "1.1.1.1",           // Cloudflare DNS
       "9.9.9.9",           // Quad9 DNS
       "208.67.222.222",    // OpenDNS
       "www.google.com",    // Google Web
       "www.cloudflare.com" // Cloudflare Web
   ];
   ```

   **Design Decision:** Use dropdown with pre-defined targets instead of free-form input. This maintains security while giving users meaningful choices.

2. **Unused Routing Module**
   - **Location:** `home/home-routing.module.ts`
   - **Issue:** Legacy file from Ionic scaffolding, not used
   - **Impact:** None, but creates confusion
   - **Recommendation:** Delete during cleanup

3. **Inconsistent App ID**
   - **Tauri:** `com.galvani.netmonitor`
   - **Capacitor:** `io.ionic.starter` (default!)
   - **Impact:** Should align before Play Store submission

4. **No Database - All Data In Memory**
   - **Issue:** `MonitorService` keeps last 50 results in BehaviorSubject
   - **Impact:** Data lost on app close - this is the main reason for SQLite enhancement

### Workarounds and Gotchas

| Issue | Workaround | Location |
|-------|------------|----------|
| Chart not updating | Force `cd.detectChanges()` after data update | `home.page.ts:80` |
| Theme not applying to chart | Use `setTimeout(() => ..., 0)` to wait for CSS | `home.page.ts:116-119` |
| CORS on web | Use `mode: 'no-cors'` for fetch (loses response) | `monitor.service.ts:80` |
| Capacitor HTTP | Use `CapacitorHttp` instead of fetch on mobile | `monitor.service.ts:73-77` |

### Platform-Specific Constraints

| Platform | Constraint | Impact |
|----------|------------|--------|
| **Tauri** | No AdMob support | Desktop is ad-free by design |
| **Tauri** | Rust security check on ping URL | Must modify to allow configurable targets |
| **Android** | Currently portrait-only | `screenOrientation="portrait"` in manifest |
| **iOS** | Manual build only | No CI/CD for iOS releases |
| **Web** | CORS blocks proper latency measurement | Development-only concern |

---

## Integration Points and External Dependencies

### External Services

| Service | Purpose | Integration Point | Notes |
|---------|---------|-------------------|-------|
| google.com | Ping target | `monitor.service.ts` | HEAD request for latency |
| ipify.org | Public IP | `ip.service.ts` | For export feature |
| AdMob | Ads | `ad.service.ts` | Mobile only |

#### ipify.org API (Public IP Tracking)

**Endpoint:** `GET https://api.ipify.org?format=json`

**Response:** `{ "ip": "203.0.113.42" }`

**Integration:**
- Called on app startup
- Called after detected reconnection (outage end)
- Current IP stored in settings table
- IP changes logged with timestamp

**Error Handling:**
- Non-blocking: doesn't block app startup
- Graceful fallback if unreachable
- App continues working offline

#### AdMob (Mobile Monetization)

**Banner Ads (Story 3.7):**
- Position: above tab bar
- Rotation: 60s visible, 120s hidden
- Smooth fade animation
- Test IDs in development

**Rewarded Video Ads (Story 3.8):**
- "Watch Ad & Export" button on Reports tab
- Export unlocked only after video completion
- Fallback: if offline/failed, allow export without ad

**Platform Exclusion:** Desktop (Tauri) has zero AdMob code/dependencies (NFR7)

#### Geolocation API (Optional)

**Purpose:** Record GPS coordinates for location verification in complaints

**Implementation:**
- Mobile: `@capacitor/geolocation` v7.x
- Desktop: `navigator.geolocation` API
- User-initiated via "Capture Location" button
- Permission handling: graceful fallback if denied

### Tauri Plugin Ecosystem

Current plugins in `Cargo.toml`:
```toml
tauri-plugin-log = "2"    # Logging (debug only)
tauri-plugin-shell = "2"  # Shell commands (unused?)
tauri-plugin-store = "2"  # Key-value storage (unused?)
```

**For SQLite:** Add `tauri-plugin-sql = { version = "2", features = ["sqlite"] }`

### Capacitor Plugin Ecosystem

Current in `package.json`:
```json
"@capacitor/app": "^7.1.1",
"@capacitor/core": "^7.4.4",
"@capacitor/haptics": "^7.0.3",
"@capacitor/keyboard": "^7.0.4",
"@capacitor/status-bar": "^7.0.4"
```

**Plugins needed for PRD:**
- `@capacitor-community/sqlite` - Database
- `@capacitor/geolocation` - GPS coordinates
- `@capacitor-community/admob` - Ads

---

## Security and Privacy

### Core Privacy Requirements (NFR4)

All user data SHALL remain **100% local** - no telemetry or data transmission to external servers.

**Allowed Exceptions:**
- `ipify.org` - Read-only IP lookup for export feature
- `AdMob` - Mobile ads only (no user data sent)

### Data Storage

| Data Type | Storage Location | Encryption |
|-----------|------------------|------------|
| Ping results | SQLite database | None (local only) |
| User settings | SQLite database | None (local only) |
| User info | SQLite database | None (local only) |
| Connection info | SQLite database | None (local only) |
| Theme preference | localStorage | None |

### Data Retention

- **Default:** 30 days
- **Configurable:** 7, 14, 30, 60, 90 days (Story 4.2)
- **Auto-cleanup:** Runs on app startup
- **Manual clear:** Users can delete all data via Reports tab (Story 3.4)

### User Control

- **Clear Data (Story 3.4):**
  - Confirmation dialog required
  - Clears: pings, outages, IP history
  - Preserves: user settings, user info, connection info

- **Export Control:**
  - Users choose when to export
  - Export files stored locally by user
  - No automatic uploads

### Offline Operation (NFR5)

App works fully offline except:
- IP lookup (silently fails if unreachable)
- AdMob ads (mobile only)
- Geolocation (optional, requires user permission)

---

## Development and Deployment

### Local Development Setup

```bash
cd netmonitor
npm install

# Web development (no Tauri/Capacitor features)
npm start                    # Serves at localhost:4200

# Desktop development (with Tauri)
npm run tauri:dev           # Starts Tauri dev server

# Android development
npx cap sync android        # Sync web assets
npx cap open android        # Open in Android Studio
# OR
ionic cap run android -l    # Live reload on device
```

### Build Commands

| Command | Output | Notes |
|---------|--------|-------|
| `npm run build` | `www/` | Angular production build |
| `npm run tauri build` | `src-tauri/target/release/bundle/` | Desktop bundles |
| `npx cap sync android` | Syncs to `android/` | Required before Android build |
| `cd android && ./gradlew assembleRelease` | APK in `app/build/outputs/` | Requires signing |

### CI/CD Pipeline

GitHub Actions workflow triggers on version tags (`v*`):
- `release-linux` - AppImage, .deb
- `release-windows` - .exe, .msi
- `release-macos` - .app, .dmg
- `release-android` - .apk, .aab

**See:** `docs/RELEASE_PROCESS.md` for full details.

---

## Testing Strategy

### Current Test Coverage

| Type | Tool | Coverage | Files |
|------|------|----------|-------|
| Unit Tests | Vitest | 80%+ | `*.spec.ts` files with comprehensive coverage |
| Integration | None | 0% | - |
| E2E | None | 0% | - |

### Required: Regression Test Suite (Story 1.0)

Before implementing any enhancement stories, a comprehensive regression test suite must be created. See PRD Story 1.0 for full specification.

**Required Tests:**

| Test ID | Component | Description |
|---------|-----------|-------------|
| RT-001 | MonitorService | Should emit ping results via results$ observable |
| RT-002 | MonitorService | Should maintain maximum 50 results in history |
| RT-003 | MonitorService | Should correctly detect Tauri platform |
| RT-004 | MonitorService | Should correctly detect Capacitor platform |
| RT-005 | HomePage | Should calculate average latency correctly |
| RT-006 | HomePage | Should calculate min/max latency correctly |
| RT-007 | HomePage | Should calculate jitter with exponential smoothing |
| RT-008 | HomePage | Should filter error results from statistics |
| RT-009 | HomePage | Should update chart data on new results |
| RT-010 | HomePage | Should toggle theme and persist to localStorage |
| RT-011 | HomePage | Should apply ion-palette-dark class for dark theme |
| RT-012 | HomePage | Should load theme preference on init |

**Coverage Target:** 80% on existing services (`monitor.service.ts`, `home.page.ts`)

### Running Tests

```bash
npm test                                           # Runs unit tests in Chrome
npm test -- --no-watch --browsers=ChromeHeadless   # CI mode
npm test -- --code-coverage                        # With coverage report
```

### Test Files

| File | Purpose |
|------|---------|
| `app.component.spec.ts` | Root component smoke test |
| `home.page.spec.ts` | Monitor page tests (to be expanded) |
| `monitor.service.spec.ts` | Core service tests (to be expanded) |

**Note:** SQLite and AdMob features will require device/emulator testing - cannot be unit tested in browser.

---

## Enhancement Impact Analysis

### Files That Will Need Modification

Based on the PRD requirements:

| File | Changes Required |
|------|------------------|
| `app.component.html` | Replace `<ion-router-outlet>` with `<ion-tabs>` structure |
| `app-routing.module.ts` | Convert to tab-based routing with child routes |
| `monitor.service.ts` | Add `DatabaseService` injection, persist pings |
| `lib.rs` | Add `tauri-plugin-sql`, consider removing hardcoded domain |
| `Cargo.toml` | Add `tauri-plugin-sql` dependency |
| `AndroidManifest.xml` | Add `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION` permissions |
| `capacitor.config.ts` | Update `appId` to match Tauri |
| `environment.ts` | Add configurable defaults for settings |

### New Files/Modules Needed

```
src/app/
├── tabs/
│   ├── tabs.page.ts           # Tab container
│   ├── tabs.page.html         # ion-tabs structure
│   └── tabs.routes.ts         # Child route definitions
├── monitor/                   # Renamed from home/
│   └── (existing files moved)
├── settings/
│   ├── settings.page.ts
│   ├── settings.page.html
│   └── settings.page.scss
├── reports/
│   ├── reports.page.ts
│   ├── reports.page.html
│   └── reports.page.scss
├── services/
│   ├── database.service.ts    # Abstract + platform implementations
│   ├── settings.service.ts    # Settings CRUD
│   ├── export.service.ts      # JSON/prompt generation
│   ├── ip.service.ts          # ipify.org integration
│   └── ad.service.ts          # AdMob wrapper
└── models/
    ├── settings.interface.ts
    ├── region.interface.ts
    ├── outage.interface.ts
    └── export-data.interface.ts
```

### Integration Considerations

1. **Database Service Abstraction**
   - Create abstract interface
   - `TauriDatabaseService` uses `@tauri-apps/plugin-sql`
   - `CapacitorDatabaseService` uses `@capacitor-community/sqlite`
   - Use `useFactory` provider to select based on platform

2. **Existing Service Compatibility**
   - `MonitorService.results$` interface must remain unchanged
   - Add database persistence as side effect, not replacement

3. **Theme Consistency**
   - All new pages must import and use existing CSS variables
   - Use `ion-palette-dark` class for dark mode

4. **AdMob Mobile-Only**
   - Use platform detection to conditionally load
   - Desktop build should have zero AdMob code/dependencies

---

## Appendix - Useful Commands

### Development

```bash
# Install dependencies
cd netmonitor && npm install

# Start dev server (web)
npm start

# Start Tauri dev
npm run tauri:dev

# Sync Capacitor
npx cap sync

# Open Android Studio
npx cap open android

# Run on connected Android device
ionic cap run android -l --external
```

### Build

```bash
# Production build
npm run build

# Tauri release build
npm run tauri build

# Android release APK
cd android && ./gradlew assembleRelease
```

### Testing

```bash
# Unit tests
npm test

# Lint
npm run lint
```

### Debugging

```bash
# Tauri logs (when running dev)
tail -f tauri.log

# Android logcat
adb logcat | grep -i netmonitor
```

---

## Coding Standards

### Angular/TypeScript Conventions

#### Component Pattern

Use **standalone components** with `inject()` for dependency injection:

```typescript
@Component({
  selector: 'app-example',
  templateUrl: 'example.page.html',
  styleUrls: ['example.page.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule, /* other imports */]
})
export class ExamplePage {
  // Use inject() instead of constructor injection
  private myService = inject(MyService);
  private cd = inject(ChangeDetectorRef);
}
```

#### Service Pattern

Use **BehaviorSubject** for reactive state management:

```typescript
@Injectable({
  providedIn: 'root'
})
export class ExampleService {
  // Private BehaviorSubject for internal state
  private _data$ = new BehaviorSubject<DataType[]>([]);

  // Public Observable for consumers
  readonly data$ = this._data$.asObservable();

  // Update state via methods
  updateData(newData: DataType[]) {
    this._data$.next(newData);
  }
}
```

#### Platform Detection

Always check platform before using platform-specific APIs:

```typescript
// For Tauri
private isTauri(): boolean {
  return !!(window as any).__TAURI__;
}

// For Capacitor native
import { Capacitor } from '@capacitor/core';
if (Capacitor.isNativePlatform()) {
  // Mobile-specific code
}

// For specific platform
if (Capacitor.getPlatform() === 'android') {
  // Android-specific code
}
```

#### Async Operations

Use `async/await` for promises, RxJS for streams:

```typescript
// One-shot operations: async/await
async loadData(): Promise<void> {
  const result = await this.database.query('SELECT * FROM table');
  this.processResult(result);
}

// Continuous streams: RxJS
this.monitorService.results$.pipe(
  map(results => this.calculateStats(results)),
  distinctUntilChanged()
).subscribe(stats => this.stats = stats);
```

### File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Page Component | `{name}.page.ts` | `settings.page.ts` |
| Service | `{name}.service.ts` | `database.service.ts` |
| Interface | `{name}.interface.ts` | `settings.interface.ts` |
| Module | `{name}.module.ts` | `app.module.ts` |
| Routing | `{name}.routes.ts` or `{name}-routing.module.ts` | `tabs.routes.ts` |
| Spec | `{name}.spec.ts` | `monitor.service.spec.ts` |

### CSS/SCSS Conventions

#### Use Ionic CSS Custom Properties

```scss
// Good - uses Ionic variables
ion-card-title {
  color: var(--stat-card-title-color);
}

// Bad - hardcoded colors
ion-card-title {
  color: #ffffff;
}
```

#### Define Custom Properties in variables.scss

```scss
:root {
  --my-custom-color: #3880ff;
}

.ion-palette-dark {
  --my-custom-color: #428cff;
}
```

#### Component-Scoped Styles

Keep styles in component `.scss` files, not global:

```scss
// home.page.scss - scoped to HomePage
.chart-container {
  position: relative;
  flex: 1;
}
```

### Rust Conventions (Tauri Backend)

#### Command Structure

```rust
#[tauri::command]
async fn my_command(
    arg: String,
    state: State<'_, AppState>
) -> Result<ReturnType, String> {
    // Implementation
}
```

#### Error Handling

Return `Result<T, String>` for commands to surface errors to frontend:

```rust
match operation {
    Ok(value) => Ok(value),
    Err(e) => Err(format!("Operation failed: {}", e))
}
```

### Testing Conventions

#### Test Requirements

- **Regression tests MUST pass** before any enhancement story is considered complete
- **New features MUST include unit tests** for all public methods
- **Coverage target:** 80% on services and business logic

#### Unit Test Structure

```typescript
describe('MonitorService', () => {
  let service: MonitorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MonitorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start monitoring', () => {
    service.startMonitoring(1000);
    expect(service['pollingSubscription']).toBeTruthy();
  });
});
```

#### Test Naming Convention

Use descriptive test names that explain the expected behavior:

```typescript
// Good
it('should calculate average latency excluding error results', () => {});
it('should emit results via results$ observable', () => {});
it('should maintain maximum 50 results in history', () => {});

// Bad
it('test1', () => {});
it('works', () => {});
```

#### Mocking Platform-Specific APIs

```typescript
import { vi } from 'vitest';

// Mock Tauri API
beforeEach(() => {
  (window as any).__TAURI__ = {
    invoke: vi.fn().mockResolvedValue({ success: true, latency: 50 })
  };
});

afterEach(() => {
  delete (window as any).__TAURI__;
});

// Mock localStorage (browser mode requires Storage.prototype)
let getItemSpy: ReturnType<typeof vi.spyOn>;
let setItemSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  getItemSpy = vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('dark');
  setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {});
});

afterEach(() => {
  getItemSpy.mockRestore();
  setItemSpy.mockRestore();
});
```

### Code Quality Rules

1. **No hardcoded strings** - Use constants or environment variables
2. **No `any` type** - Define proper interfaces
3. **No unused imports** - Clean up after refactoring
4. **Document public APIs** - JSDoc for service methods
5. **Handle errors** - Never swallow errors silently
6. **Platform checks** - Always verify platform before native calls

---

## Next Steps

### Implementation Sequence

1. **Story 1.0: Regression Test Suite** (PREREQUISITE)
   - Create comprehensive tests for existing functionality
   - Verify MonitorService, HomePage, theme toggle
   - Must pass before any enhancement work begins

2. **Epic 1: Foundation** (Stories 1.1-1.5)
   - DatabaseService abstraction
   - SQLite schema and migrations
   - Tab navigation structure

3. **Epic 2: Configuration** (Stories 2.1-2.6)
   - Settings service
   - Settings tab UI

4. **Epic 3: Reporting** (Stories 3.1-3.8)
   - Reports tab with statistics
   - Export functionality
   - AdMob integration (mobile)

5. **Epic 4: Polish** (Stories 4.1-4.2)
   - Monitoring duration display
   - Retention configuration

### Developer Handoff

**Before starting implementation:**
1. Read this architecture document completely
2. Review PRD at `docs/prd.md` for detailed story specifications
3. Set up development environment (see Development and Deployment section)
4. Run existing tests: `npm test`

**Key integration checkpoints:**
- After Story 1.0: All regression tests pass
- After Story 1.3: Ping data persists to SQLite
- After Story 1.4: Tab navigation works without breaking Monitor
- After Story 2.1: Settings persist across app restarts
- After Story 3.5: Export generates valid JSON

**Platform testing required:**
- Test on web (development)
- Test on Tauri (desktop)
- Test on Android emulator/device
- (Optional) Test on iOS simulator/device

### Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/prd.md` | Product requirements and story specifications |
| `docs/references/POST-MVP-ROADMAP.md` | Original feature roadmap |
| `docs/references/RELEASE_PROCESS.md` | Build and release procedures |
