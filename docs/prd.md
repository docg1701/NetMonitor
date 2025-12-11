# NetMonitor Post-MVP Enhancement PRD

## Document Information

| Field | Value |
|-------|-------|
| **Version** | 0.1 |
| **Status** | Draft |
| **Created** | 2025-12-10 |
| **Last Updated** | 2025-12-10 |

---

## 1. Intro Project Analysis and Context

### 1.1 Existing Project Overview

#### Analysis Source
- IDE-based fresh analysis combined with user-provided documentation (`POST-MVP-ROADMAP.md`)

#### Current Project State
NetMonitor is a **cross-platform network latency monitoring tool** at version **1.0.4 (MVP)**. It provides:
- Real-time ping monitoring with 1-second intervals
- Visual latency chart (last 50 data points)
- Live statistics: current, avg, min, max, jitter
- Dark/light theme toggle
- Cross-platform support: Desktop (Tauri/Rust) + Mobile (Capacitor)

**Key architectural insight:** The app currently has **no data persistence** - all monitoring data exists only in memory and is lost when the app closes.

---

### 1.2 Available Documentation Analysis

| Documentation | Status |
|---------------|--------|
| Tech Stack Documentation | README.md |
| Source Tree/Architecture | Not documented |
| Coding Standards | Not documented |
| API Documentation | N/A (no external API) |
| External API Documentation | POST-MVP-ROADMAP.md |
| UX/UI Guidelines | Not documented |
| Technical Debt Documentation | Not documented |

---

### 1.3 Enhancement Scope Definition

#### Enhancement Type
- [x] **New Feature Addition** (Settings tab, Reports tab, AI export)
- [x] **Integration with New Systems** (SQLite, AdMob, Geolocation API)
- [x] **UI/UX Overhaul** (Tab-based navigation)

#### Enhancement Description
Transform NetMonitor from a real-time-only monitor into a comprehensive network quality documentation tool by adding **data persistence (SQLite)**, **configurable settings**, **statistical reports**, and **AI-powered export** for consumer rights complaints. Mobile version will include **AdMob monetization**.

#### Impact Assessment
- [x] **Significant Impact** (substantial existing code changes)

**Rationale:** The enhancement requires:
- Adding SQLite persistence layer (Tauri + Capacitor plugins)
- Restructuring UI from single-page to tab-based navigation
- Adding 2 new major screens (Settings, Reports)
- Integrating external services (ipify.org, AdMob, Geolocation)

---

### 1.4 Goals and Background Context

#### Goals
- Enable users to collect long-term network quality data as evidence for consumer complaints
- Provide multi-region support (Brazil, US, EU, UK) with localized regulatory information
- Generate AI-ready exports (JSON + prompt) for automated report/document generation
- Monetize mobile app through non-intrusive AdMob ads

#### Background Context
The MVP established NetMonitor as a functional real-time monitoring tool. However, users need to **document network issues over time** to file complaints with regulatory bodies (ANATEL, FCC, Ofcom, etc.). Without persistence, users lose all evidence when closing the app.

The POST-MVP roadmap addresses this by adding SQLite storage, configuration options, and an innovative AI-export feature that leverages ChatGPT/Claude/Gemini to generate professional complaint documents - avoiding complex PDF generation in the app itself.

---

### 1.5 Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial Draft | 2025-12-10 | 0.1 | First draft based on POST-MVP-ROADMAP | PM Agent |

---

## 2. Requirements

### 2.1 Functional Requirements

| ID | Requirement |
|----|-------------|
| **FR1** | The app SHALL persist all ping results (timestamp, latency_ms, success, target) to a local SQLite database |
| **FR2** | The app SHALL provide a tabbed navigation structure with Monitor, Settings, and Reports tabs |
| **FR3** | The Settings tab SHALL allow users to select ping target from a pre-defined dropdown list and configure ping interval |
| **FR4** | The Settings tab SHALL allow users to select their country/region (Brazil, US, EU, UK) which determines applicable regulatory bodies and document templates |
| **FR5** | The Settings tab SHALL collect optional user information (name, document ID, address, phone) for report personalization |
| **FR6** | The Settings tab SHALL collect connection information (provider, plan name, contracted speed, connection type) |
| **FR7** | The Reports tab SHALL display monitoring statistics: period, total pings, uptime %, latency stats, outages count, total downtime |
| **FR8** | The Reports tab SHALL provide a "Clear Data" action with confirmation dialog |
| **FR9** | The Reports tab SHALL export monitoring data as JSON file (`netmonitor_dados.json`) |
| **FR10** | The Reports tab SHALL export an AI prompt file (`netmonitor_prompt.txt`) with instructions for LLM-based report generation |
| **FR11** | The app SHALL periodically collect and store the user's public IP address (via ipify.org API) |
| **FR12** | The app SHALL request and store GPS coordinates (with user permission) for location verification |
| **FR13** | The app SHALL detect and record outages with start/end times and IP changes |
| **FR14** | (Mobile only) The app SHALL display rotating banner ads (60s on / 120s off cycle) |
| **FR15** | (Mobile only) The app SHALL require users to watch a rewarded video ad before exporting reports |

---

### 2.2 Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| **NFR1** | SQLite operations SHALL NOT block the UI thread or impact real-time monitoring performance |
| **NFR2** | The app SHALL maintain existing startup time (<2 seconds to interactive) |
| **NFR3** | Database size SHALL be manageable - automatic cleanup of data older than configurable retention period (default: 30 days) |
| **NFR4** | All user data SHALL remain 100% local - no telemetry or data transmission to external servers (except ipify.org for IP lookup and AdMob for ads) |
| **NFR5** | The app SHALL work offline (except features requiring network: IP lookup, ads) |
| **NFR6** | Export files SHALL be valid JSON parseable by any LLM |
| **NFR7** | Desktop version (Tauri) SHALL NOT include any advertising |
| **NFR8** | **Regression Testing**: Each epic SHALL pass the regression test suite before being considered complete, ensuring existing functionality remains intact |

---

### 2.3 Testing Requirements

| ID | Requirement |
|----|-------------|
| **TR1** | A regression test suite SHALL be created before Epic 1 implementation begins |
| **TR2** | Regression tests SHALL cover: ping measurement accuracy, chart updates, statistics calculation, theme toggle, and app startup |
| **TR3** | All regression tests SHALL pass on both Tauri (desktop) and Capacitor (mobile) platforms |
| **TR4** | Each story SHALL include unit tests for new functionality |
| **TR5** | Integration tests SHALL verify database operations don't impact real-time monitoring |

---

### 2.4 Compatibility Requirements

| ID | Requirement |
|----|-------------|
| **CR1** | **Existing API Compatibility**: The `MonitorService` interface (`startMonitoring`, `stopMonitoring`, `results$`) SHALL remain unchanged to avoid breaking the Monitor tab |
| **CR2** | **Database Schema Compatibility**: Initial schema SHALL support forward migration - use versioned migrations from day one |
| **CR3** | **UI/UX Consistency**: New tabs SHALL follow existing Ionic component patterns and dark/light theme support |
| **CR4** | **Platform Parity**: Core functionality (persistence, settings, reports) SHALL work identically on Desktop (Tauri) and Mobile (Capacitor), with ads being the only mobile-specific feature |

---

## 3. User Interface Enhancement Goals

### 3.1 Integration with Existing UI

**Current UI Patterns:**
- Ionic 8 components with standalone Angular components
- Dark/light theme via `ion-palette-dark` class on `<body>`
- CSS custom properties for theming (`--chart-line-color`, `--chart-fill-color`)
- Single-page layout with `ion-header`, `ion-content`, `ion-card` structure
- Chart.js for data visualization

**Integration Approach:**
- Convert from single-page to `ion-tabs` navigation (standard Ionic pattern)
- Existing Monitor page becomes first tab with minimal changes
- New pages follow same standalone component pattern
- Reuse existing theme infrastructure - all new components will respect dark/light mode
- Extend CSS custom properties as needed for new components

---

### 3.2 Modified/New Screens and Views

| Screen | Type | Description |
|--------|------|-------------|
| **App Shell** | Modified | Add `ion-tabs` wrapper with 3 tabs: Monitor, Settings, Reports |
| **Monitor Tab** | Modified | Current `home.page` relocated to tab; add "Monitoring duration" card |
| **Settings Tab** | New | Form-based configuration with sections for monitoring, region, user data, connection |
| **Reports Tab** | New | Statistics display, data management actions, export functionality |

#### Monitor Tab Changes
```
+------------------------------------------+
| NetMonitor                       [dark]  |  <- Existing header
+------------------------------------------+
|  +------------------------------------+  |
|  | Monitoring: 2h 34m 12s             |  |  <- NEW: Duration card
|  +------------------------------------+  |
|                                          |
|  [Existing chart and stats cards...]     |
|                                          |
+------------------------------------------+
|  [Monitor]    [Settings]    [Reports]    |  <- NEW: Tab bar
+------------------------------------------+
```

#### Settings Tab Layout
```
+------------------------------------------+
| Settings                                 |
+------------------------------------------+
|  > Monitoring                            |
|  +------------------------------------+  |
|  | Ping Target    [Google DNS v     ]  |  <- Dropdown
|  | Interval (s)   [5               ]  |  |
|  +------------------------------------+  |
|                                          |
|  > Region                                |
|  +------------------------------------+  |
|  | BR Brasil                        * |  |
|  | US United States                   |  |
|  | EU European Union                  |  |
|  | GB United Kingdom                  |  |
|  +------------------------------------+  |
|                                          |
|  > Your Information (for reports)        |
|  +------------------------------------+  |
|  | Name           [                 ]  |  |
|  | CPF            [                 ]  |  <- Dynamic by region
|  | Address        [                 ]  |  |
|  | Phone          [                 ]  |  |
|  +------------------------------------+  |
|                                          |
|  > Connection Details                    |
|  +------------------------------------+  |
|  | Provider       [                 ]  |  |
|  | Plan           [                 ]  |  |
|  | Speed (Mbps)   [                 ]  |  |
|  | Type           [Fiber v         ]  |  |
|  +------------------------------------+  |
|                                          |
|  [Restore Defaults]                      |
+------------------------------------------+
|  [Monitor]    [Settings]    [Reports]    |
+------------------------------------------+
```

#### Reports Tab Layout
```
+------------------------------------------+
| Reports                                  |
+------------------------------------------+
|  Statistics                              |
|  +------------------------------------+  |
|  | Period: Dec 1 - Dec 10, 2025      |  |
|  | Total pings: 15,234               |  |
|  | Uptime: 98.38%                    |  |
|  | Avg latency: 45ms                 |  |
|  | Min/Max: 12ms / 890ms             |  |
|  | Outages: 3                        |  |
|  | Total downtime: 23.5 min          |  |
|  +------------------------------------+  |
|                                          |
|  Data Management                         |
|  +------------------------------------+  |
|  |        [Clear All Data]           |  |
|  +------------------------------------+  |
|                                          |
|  AI Export                               |
|  +------------------------------------+  |
|  |  Generate reports using AI         |  |
|  |  (ChatGPT, Claude, Gemini)         |  |
|  |                                    |  |
|  |  [Watch Ad & Export]               |  <- Mobile only
|  |  [Export for AI]                   |  <- Desktop
|  +------------------------------------+  |
+------------------------------------------+
|  [Monitor]    [Settings]    [Reports]    |
+------------------------------------------+
```

---

### 3.3 UI Consistency Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Component Library** | Use only Ionic 8 components (`ion-card`, `ion-item`, `ion-input`, `ion-select`, `ion-button`, `ion-list`, `ion-accordion`) |
| **Theme Support** | All new components MUST respect `ion-palette-dark` toggle |
| **Typography** | Use Ionic default typography - no custom fonts |
| **Icons** | Use Ionicons (already imported) for all icons |
| **Spacing** | Follow Ionic padding/margin standards via CSS utilities |
| **Forms** | Use `ion-item` + `ion-input`/`ion-select` pattern for all form fields |
| **Buttons** | Primary actions: `ion-button fill="solid"`, Secondary: `fill="outline"`, Destructive: `color="danger"` |
| **Feedback** | Use `ion-toast` for success/error messages, `ion-alert` for confirmations |

---

## 4. Technical Constraints and Integration Requirements

### 4.1 Existing Technology Stack

| Category | Technology | Version | Notes |
|----------|------------|---------|-------|
| **Languages** | TypeScript, Rust | TS 5.9, Rust 1.77+ | Rust only for Tauri backend |
| **Frontend Framework** | Angular | 21.0.0 | Standalone components, no NgModules |
| **UI Framework** | Ionic | 8.0.0 | Dark theme via `ion-palette-dark` |
| **Desktop Runtime** | Tauri | 2.9.x | Rust backend with `@tauri-apps/api` |
| **Mobile Runtime** | Capacitor | 7.4.4 | Native Android/iOS bridges |
| **Charts** | Chart.js + ng2-charts | 4.5.1 / 8.0.0 | Line charts for latency |
| **State Management** | RxJS BehaviorSubject | 7.8.0 | Service-based reactive state |
| **Build Tool** | Angular CLI | 21.0.0 | Webpack under the hood |

**New Dependencies Required:**

| Platform | Package | Version | Purpose |
|----------|---------|---------|---------|
| Tauri (Rust) | `tauri-plugin-sql` | 2.x | SQLite for desktop |
| Tauri (JS) | `@tauri-apps/plugin-sql` | 2.3.x | SQLite JS bindings |
| Capacitor | `@capacitor-community/sqlite` | 7.x | SQLite for mobile |
| Capacitor | `@capacitor/geolocation` | 7.x | GPS coordinates |
| Capacitor | `@capacitor-community/admob` | 6.x | Mobile ads |

---

### 4.2 Integration Approach

#### Database Integration Strategy

```
+-------------------------------------------------------------+
|                    DatabaseService                          |
|  +-------------------------------------------------------+  |
|  |              Abstract Interface                       |  |
|  |  - init(): Promise<void>                              |  |
|  |  - execute(): Promise<void>                           |  |
|  |  - select(): Promise<T[]>                             |  |
|  |  - close(): Promise<void>                             |  |
|  +-------------------------------------------------------+  |
|                           |                                 |
|              +------------+------------+                    |
|              v                         v                    |
|  +---------------------+   +---------------------+          |
|  |  TauriSqlService    |   | CapacitorSqlService |          |
|  |  (tauri-plugin-sql) |   | (@capacitor/sqlite) |          |
|  +---------------------+   +---------------------+          |
+-------------------------------------------------------------+
```

**Strategy:** Create an abstract `DatabaseService` with platform-specific implementations. Use Angular's dependency injection with `useFactory` to provide the correct implementation based on platform detection.

#### API Integration Strategy

| External Service | Purpose | Integration Point |
|------------------|---------|-------------------|
| `ipify.org` | Public IP lookup | New `IpService` - called on app start + after detected reconnection |
| `navigator.geolocation` | GPS coordinates | Capacitor Geolocation plugin - requested once in Settings |
| AdMob | Monetization | `AdService` - mobile-only, initialized on app start |

**No backend API** - all data stays local. External calls are read-only lookups.

#### Frontend Integration Strategy

```
src/app/
├── app.component.ts          # Add ion-tabs wrapper
├── app.routes.ts             # NEW: Tab routing configuration
├── tabs/
│   ├── tabs.page.ts          # NEW: Tab container
│   └── tabs.routes.ts        # NEW: Child routes
├── monitor/                  # RENAMED from home/
│   ├── monitor.page.ts       # Existing home.page relocated
│   └── monitor.page.html
├── settings/                 # NEW
│   ├── settings.page.ts
│   └── settings.page.html
├── reports/                  # NEW
│   ├── reports.page.ts
│   └── reports.page.html
├── services/
│   ├── monitor.service.ts    # Existing - add DB persistence
│   ├── tauri.service.ts      # Existing
│   ├── database.service.ts   # NEW: Abstract DB service
│   ├── settings.service.ts   # NEW: Settings management
│   ├── export.service.ts     # NEW: JSON/prompt generation
│   ├── ip.service.ts         # NEW: Public IP lookup
│   └── ad.service.ts         # NEW: AdMob wrapper (mobile)
└── models/
    ├── ping-result.interface.ts  # Existing
    ├── settings.interface.ts     # NEW
    ├── region.interface.ts       # NEW
    └── export-data.interface.ts  # NEW
```

#### Testing Integration Strategy

| Test Type | Tool | Focus |
|-----------|------|-------|
| Unit Tests | Vitest | Services, components |
| E2E Tests | None currently | Consider adding Playwright for tab navigation |
| Manual Testing | Device testing | Platform-specific features (SQLite, AdMob) |

**Constraint:** SQLite and AdMob require device/emulator testing - cannot be fully tested in browser.

---

### 4.3 Code Organization and Standards

**File Structure Approach:**
- Feature-based folders (`monitor/`, `settings/`, `reports/`)
- Shared services in `services/`
- Interfaces in `models/`
- Platform-specific code isolated in service implementations

**Naming Conventions:**
- Components: `feature.page.ts` (Ionic convention)
- Services: `feature.service.ts`
- Interfaces: `feature.interface.ts`
- Constants: `UPPER_SNAKE_CASE`

**Coding Standards:**
- Standalone components (no NgModules)
- Inject dependencies via `inject()` function (modern Angular)
- Use `async/await` for async operations
- RxJS for reactive streams, Promises for one-shot operations
- Strict TypeScript (`strict: true` in tsconfig)

**Documentation Standards:**
- JSDoc for public service methods
- Inline comments only for non-obvious logic
- README updates for new features

---

### 4.4 Deployment and Operations

**Build Process Integration:**
- No changes to existing build pipeline
- `npm run build` -> Angular build to `www/`
- `npm run tauri build` -> Desktop bundles
- `npx cap sync` -> Mobile sync

**Deployment Strategy:**
- Continue existing release process (see `docs/RELEASE_PROCESS.md`)
- SQLite migrations run on app startup (transparent to users)
- No server-side deployment

**Monitoring and Logging:**
- Existing Tauri logging plugin (`tauri-plugin-log`)
- Add SQLite operation logging for debugging
- No external monitoring/analytics (privacy commitment)

**Configuration Management:**
- User settings stored in SQLite `settings` table
- App defaults defined in code constants
- No remote configuration

---

### 4.5 Risk Assessment and Mitigation

#### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQLite plugin incompatibility between Tauri/Capacitor | Medium | High | Use abstract service layer; test both platforms early |
| AdMob initialization failures on older devices | Low | Medium | Graceful fallback - allow export without ad if ad fails |
| Geolocation permission denied | Medium | Low | Make GPS optional; app works without it |
| Large database size over time | Medium | Medium | Implement auto-cleanup; data retention settings |

#### Integration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing Monitor functionality during refactor | Medium | High | Refactor incrementally; keep existing service interfaces |
| Theme inconsistency in new tabs | Low | Medium | Reuse existing CSS variables; test both themes |
| Tab navigation breaking deep links | Low | Low | No deep links currently; not a concern |

#### Deployment Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration failures on existing installations | Low | High | Version migrations carefully; test upgrade path |
| App store rejection due to AdMob compliance | Low | Medium | Follow AdMob policies strictly; proper consent flows |

#### Mitigation Strategies

1. **Incremental Development**: Implement Phase 1 (SQLite) first, validate on both platforms before proceeding
2. **Feature Flags**: Consider environment-based flags for mobile-only features (ads)
3. **Database Versioning**: Use migration system from day one, even for initial schema
4. **Platform Abstraction**: All platform-specific code behind interfaces for easy testing/mocking

---

## 5. Epic Structure

### Epic Approach Decision

**Decision: 4 Epics**

| Epic | Phases Covered | Rationale |
|------|----------------|-----------|
| **Epic 1: Foundation** | Phase 1 (SQLite) + Tab Navigation | Must be complete before any other work; establishes data layer |
| **Epic 2: Configuration** | Phase 2 (Settings Tab) | Standalone feature, can be developed once tabs exist |
| **Epic 3: Reporting & Export** | Phase 3 (Reports) + Phase 4 (AdMob) | Core value delivery - grouped because AdMob gates export |
| **Epic 4: Polish** | Phase 5 (UX) | Enhancement to existing features |

**Rationale:**
- SQLite + Tab navigation forms the foundational infrastructure (Epic 1)
- Settings is an independent feature module (Epic 2)
- Reports and AdMob share the export flow - splitting them would create incomplete features (Epic 3)
- UX polish can be delivered as a final enhancement pass (Epic 4)

---

## 6. Epic Details & Stories

---

## Epic 1: Foundation - SQLite Persistence & Tab Navigation

**Epic Goal:** Establish the data persistence layer and restructure the app from single-page to tab-based navigation, enabling all subsequent features.

**Integration Requirements:**
- SQLite must work on both Tauri (desktop) and Capacitor (mobile)
- Existing Monitor functionality must remain fully operational
- Tab navigation must support lazy loading for performance

---

### Story 1.0: Create Regression Test Suite (PREREQUISITE)

> **As a** developer,
> **I want** a comprehensive regression test suite for existing functionality,
> **so that** I can verify no features are broken during the enhancement implementation.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Unit tests for `MonitorService`: `startMonitoring()`, `stopMonitoring()`, `measureLatency()`, `results$` observable |
| AC2 | Unit tests for `HomePage`: stats calculation (`updateStats()`), chart data binding, theme toggle |
| AC3 | Tests verify ping result processing: ok status, error status, null latency handling |
| AC4 | Tests verify statistics calculation: average, min, max, jitter with exponential smoothing |
| AC5 | Tests verify chart updates with new data points (50-point history limit) |
| AC6 | Tests verify dark/light theme toggle persists to localStorage |
| AC7 | Test coverage report generated with minimum 80% coverage on existing services |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | All tests pass on web (Chrome/Chromium headless) |
| IV2 | Tests can run in CI pipeline (`npm test -- --no-watch --browsers=ChromeHeadless`) |
| IV3 | Test execution time < 30 seconds |

#### Test Cases Specification

| Test ID | Component | Test Description |
|---------|-----------|------------------|
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

---

### Story 1.1: Create Abstract Database Service Layer

> **As a** developer,
> **I want** a platform-agnostic database service interface,
> **so that** I can write business logic once and have it work on both desktop and mobile.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | `DatabaseService` abstract class defines methods: `init()`, `execute()`, `select()`, `close()` |
| AC2 | `TauriDatabaseService` implements the interface using `@tauri-apps/plugin-sql` |
| AC3 | `CapacitorDatabaseService` implements the interface using `@capacitor-community/sqlite` |
| AC4 | Angular DI provides correct implementation based on platform detection |
| AC5 | Database file is created at platform-appropriate location (app data directory) |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Existing `MonitorService` continues to function without database (no regression) |
| IV2 | Platform detection correctly identifies Tauri vs Capacitor vs Web |
| IV3 | Service initializes without blocking app startup |

---

### Story 1.2: Implement SQLite Schema and Migrations

> **As a** developer,
> **I want** a versioned database schema with migration support,
> **so that** future schema changes can be applied safely to existing installations.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | `pings` table created with columns: `id`, `timestamp`, `latency_ms`, `success`, `target` |
| AC2 | `settings` table created with columns: `key`, `value` |
| AC3 | Index created on `pings.timestamp` for query performance |
| AC4 | Migration system tracks schema version in database |
| AC5 | Migrations run automatically on app startup |
| AC6 | Migration failures are logged and don't crash the app |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Fresh install creates schema correctly on both platforms |
| IV2 | App upgrade with existing database applies migrations without data loss |
| IV3 | Database operations complete within acceptable time (<100ms for single inserts) |

---

### Story 1.3: Integrate Ping Persistence into MonitorService

> **As a** user,
> **I want** my ping results automatically saved to the database,
> **so that** I can view historical data and generate reports later.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Each ping result is persisted to SQLite immediately after measurement |
| AC2 | Database writes are non-blocking (don't delay next ping) |
| AC3 | Failed database writes are logged but don't stop monitoring |
| AC4 | Ping results include all fields: timestamp, latency_ms, success (boolean), target |
| AC5 | Historical data survives app restart |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Real-time chart continues updating at same refresh rate |
| IV2 | Memory usage remains stable (no accumulation from DB operations) |
| IV3 | App startup time not significantly impacted (<500ms additional) |

---

### Story 1.4: Implement Tab-Based Navigation Structure

> **As a** user,
> **I want** tab navigation at the bottom of the screen,
> **so that** I can easily switch between Monitor, Settings, and Reports.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | `ion-tabs` component with 3 tabs: Monitor, Settings, Reports |
| AC2 | Tab icons use Ionicons: `pulse-outline`, `settings-outline`, `document-text-outline` |
| AC3 | Active tab is visually highlighted |
| AC4 | Tab routes are lazy-loaded for performance |
| AC5 | Current Monitor page relocated to `/tabs/monitor` route |
| AC6 | Placeholder pages created for Settings and Reports tabs |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Existing Monitor functionality works identically in new tab location |
| IV2 | Theme toggle (dark/light) continues working across all tabs |
| IV3 | Navigation state preserved when switching tabs (monitoring continues) |

---

### Story 1.5: Add Data Retention and Cleanup

> **As a** user,
> **I want** old monitoring data automatically cleaned up,
> **so that** the database doesn't grow indefinitely and slow down my device.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Default retention period is 30 days |
| AC2 | Cleanup runs on app startup (after migrations) |
| AC3 | Cleanup deletes pings older than retention period |
| AC4 | Cleanup is logged with count of deleted records |
| AC5 | Retention period will be configurable in Settings (future story) |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Recent data (<30 days) is preserved after cleanup |
| IV2 | Cleanup completes within reasonable time (<2s for 100k records) |
| IV3 | App remains responsive during cleanup operation |

---

## Epic 2: Configuration - Settings Tab

**Epic Goal:** Provide users with a comprehensive settings interface to configure monitoring parameters, regional preferences, and personal/connection information for reports.

**Integration Requirements:**
- Settings must persist to SQLite
- Settings changes must be reflected immediately in monitoring behavior
- Region selection must dynamically adjust form fields

---

### Story 2.1: Create Settings Service and Data Model

> **As a** developer,
> **I want** a centralized settings service,
> **so that** all app components can access and react to configuration changes.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | `SettingsService` provides reactive access to all settings via `settings$` Observable |
| AC2 | Settings interface defines: monitoring config, region, user info, connection info |
| AC3 | Default values provided for all settings |
| AC4 | Settings loaded from SQLite on app startup |
| AC5 | Settings changes persisted immediately to SQLite |
| AC6 | `MonitorService` reacts to ping target/interval changes |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | App starts with defaults if no settings exist |
| IV2 | Settings survive app restart |
| IV3 | Changing ping interval immediately affects monitoring (after restart monitoring) |

---

### Story 2.2: Implement Monitoring Configuration Section

> **As a** user,
> **I want** to configure the ping target and interval,
> **so that** I can monitor my specific network conditions.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Dropdown selector for ping target with pre-defined options (see table below) |
| AC2 | Input field for ping interval (seconds) with min/max validation (1-60s) |
| AC3 | Default values: target `Google DNS (8.8.8.8)`, interval `5` seconds |
| AC4 | Changes saved on selection/blur |
| AC5 | "Restore Defaults" button resets monitoring settings |
| AC6 | Toast notification confirms settings saved |

**Pre-defined Ping Targets (Dropdown Options):**

| Label | Value | Protocol | Rationale |
|-------|-------|----------|-----------|
| Google DNS (8.8.8.8) | `8.8.8.8` | ICMP/HTTP | Most reliable, global presence |
| Cloudflare DNS (1.1.1.1) | `1.1.1.1` | ICMP/HTTP | Known for low latency |
| Quad9 DNS (9.9.9.9) | `9.9.9.9` | ICMP/HTTP | Security-focused alternative |
| OpenDNS (208.67.222.222) | `208.67.222.222` | ICMP/HTTP | Popular enterprise choice |
| Google Web | `www.google.com` | HTTP HEAD | Web-based measurement |
| Cloudflare Web | `www.cloudflare.com` | HTTP HEAD | Web-based alternative |

**Note:** This approach maintains backend security by whitelisting allowed targets in Rust code, while giving users meaningful choices.

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Dropdown displays all pre-defined targets correctly |
| IV2 | Saved settings persist after app restart |
| IV3 | Monitor tab uses new settings when monitoring restarted |
| IV4 | Rust backend accepts all whitelisted targets |

---

### Story 2.3: Implement Region Selection with Dynamic Forms

> **As a** user,
> **I want** to select my country/region,
> **so that** reports include the correct regulatory bodies and document templates.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Radio group with 4 options: Brasil, United States, European Union, United Kingdom |
| AC2 | Selection persisted to settings |
| AC3 | Region data model includes: country_code, country_name, regulatory_body, consumer_protection, applicable_law |
| AC4 | User info form fields change based on region (document type, phone format) |
| AC5 | Default region based on device locale (if detectable), otherwise Brasil |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Region change immediately updates user info form fields |
| IV2 | Export includes correct region metadata |
| IV3 | Region survives app restart |

---

### Story 2.4: Implement User Information Form

> **As a** user,
> **I want** to enter my personal information,
> **so that** exported reports are personalized with my details for regulatory complaints.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Fields: name, document (type varies by region), address, phone |
| AC2 | Document field label changes by region: CPF (BR), SSN (US), National ID (EU), NIN (UK) |
| AC3 | Phone field includes country code prefix |
| AC4 | All fields are optional (don't block app usage) |
| AC5 | Basic format validation for document numbers (CPF checksum for Brazil) |
| AC6 | Data saved on blur |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Validation errors displayed inline without blocking save |
| IV2 | Partial data can be saved (user can fill incrementally) |
| IV3 | Data included in export JSON when present |

---

### Story 2.5: Implement Connection Information Form

> **As a** user,
> **I want** to enter my ISP and plan details,
> **so that** reports include context about my contracted service.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Fields: provider name, plan name, contracted speed (Mbps), connection type, contract number (optional) |
| AC2 | Connection type is dropdown: Fiber, Cable, DSL, Wireless, Satellite, Other |
| AC3 | Speed field is numeric with Mbps suffix |
| AC4 | All fields optional |
| AC5 | Data saved on blur |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Connection info included in export JSON |
| IV2 | Data survives app restart |
| IV3 | No impact on monitoring functionality |

---

### Story 2.6: Implement Geolocation Capture

> **As a** user,
> **I want** to optionally capture my GPS coordinates,
> **so that** reports can verify my location matches my declared address.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | "Capture Location" button in user info section |
| AC2 | Requests geolocation permission on button press |
| AC3 | Displays captured coordinates and accuracy |
| AC4 | "Clear Location" option to remove stored coordinates |
| AC5 | Uses `@capacitor/geolocation` on mobile, `navigator.geolocation` on desktop |
| AC6 | Graceful handling if permission denied |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | App functions normally if location permission denied |
| IV2 | Coordinates included in export when captured |
| IV3 | Location capture works on both desktop and mobile |

---

## Epic 3: Reporting & Export - Reports Tab + AdMob

**Epic Goal:** Enable users to view monitoring statistics, export data for AI-powered report generation, and monetize mobile app through non-intrusive ads.

**Integration Requirements:**
- Statistics must aggregate data from SQLite
- Export format must match POST-MVP-ROADMAP specification exactly
- AdMob must not impact desktop version

---

### Story 3.1: Implement Reports Tab with Statistics Display

> **As a** user,
> **I want** to see aggregated statistics of my monitoring data,
> **so that** I can understand my network quality at a glance.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Display monitoring period (first ping to last ping dates) |
| AC2 | Display total ping count |
| AC3 | Display uptime percentage |
| AC4 | Display latency stats: average, minimum, maximum |
| AC5 | Display outage count and total downtime |
| AC6 | Statistics refresh when tab becomes active |
| AC7 | Empty state shown if no data exists |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Statistics match actual database contents |
| IV2 | Tab switch doesn't interrupt active monitoring |
| IV3 | Performance acceptable with large datasets (>100k pings) |

---

### Story 3.2: Implement Outage Detection and Recording

> **As a** user,
> **I want** network outages automatically detected and recorded,
> **so that** I have evidence of service interruptions.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Outage defined as 3+ consecutive failed pings |
| AC2 | Outage record includes: start time, end time, duration |
| AC3 | `outages` table added to schema (migration) |
| AC4 | Outages list displayed in Reports tab (most recent first) |
| AC5 | Each outage shows date/time and duration |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Outage detection doesn't impact monitoring performance |
| IV2 | Outages included in export JSON |
| IV3 | Schema migration preserves existing ping data |

---

### Story 3.3: Implement Public IP Tracking

> **As a** user,
> **I want** my public IP address recorded,
> **so that** reports can document IP changes that may indicate reconnections.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | `IpService` fetches IP from `https://api.ipify.org?format=json` |
| AC2 | IP checked on app startup and after detected reconnection (outage end) |
| AC3 | Current IP stored in settings |
| AC4 | IP changes logged with timestamp |
| AC5 | Outage records include IP before/after when available |
| AC6 | Graceful handling if ipify.org unreachable |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | IP lookup doesn't block app startup |
| IV2 | App works fully offline (IP lookup silently fails) |
| IV3 | IP data included in export JSON |

---

### Story 3.4: Implement Data Clear Functionality

> **As a** user,
> **I want** to clear all monitoring data,
> **so that** I can start fresh or free up storage.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | "Clear All Data" button in Reports tab |
| AC2 | Confirmation dialog before deletion |
| AC3 | Clears: pings, outages, IP history |
| AC4 | Does NOT clear: user settings, user info, connection info |
| AC5 | Success toast after completion |
| AC6 | Statistics display updates to empty state |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Settings preserved after data clear |
| IV2 | Monitor tab can immediately start collecting new data |
| IV3 | Clear operation completes in reasonable time |

---

### Story 3.5: Implement JSON Export Generation

> **As a** user,
> **I want** to export my monitoring data as JSON,
> **so that** I can use it with AI assistants for report generation.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Export generates `netmonitor_dados.json` matching POST-MVP-ROADMAP spec |
| AC2 | Includes: app version, export date, region, user info, connection info |
| AC3 | Includes: period, summary statistics, outages array |
| AC4 | Includes: hourly_summary array for trend analysis |
| AC5 | File saved to device downloads folder |
| AC6 | Success toast with file location |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Generated JSON is valid and parseable |
| IV2 | Large datasets export without app freeze (use async/chunked) |
| IV3 | Export works on both desktop and mobile |

---

### Story 3.6: Implement AI Prompt Export

> **As a** user,
> **I want** an AI prompt file exported alongside my data,
> **so that** I have clear instructions for using the data with ChatGPT/Claude/Gemini.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Export generates `netmonitor_prompt.txt` with instructions |
| AC2 | Prompt content matches POST-MVP-ROADMAP specification |
| AC3 | Prompt language matches selected region (Portuguese for BR, English for others) |
| AC4 | Both files exported together as single action |
| AC5 | Clear user instructions in the prompt file |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Prompt file is human-readable plain text |
| IV2 | Region-specific complaint bodies mentioned in prompt |
| IV3 | Export action creates both files in same location |

---

### Story 3.7: Implement AdMob Banner Ads (Mobile Only)

> **As a** mobile user,
> **I want** to see non-intrusive banner ads,
> **so that** the app can be monetized while I use it for free.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Banner ad displayed above tab bar on mobile |
| AC2 | Ad rotation: 60 seconds visible, 120 seconds hidden |
| AC3 | Smooth fade animation on show/hide |
| AC4 | Uses test ad IDs in development |
| AC5 | No ads on desktop (Tauri) version |
| AC6 | Ad failures logged but don't crash app |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Banner doesn't overlap or shift tab content |
| IV2 | Monitoring performance unaffected by ad loading |
| IV3 | Desktop build has no AdMob code/dependencies |

---

### Story 3.8: Implement Rewarded Ad for Export (Mobile Only)

> **As a** mobile user,
> **I want** to watch a video ad to unlock export,
> **so that** I can access the export feature for free while supporting the app.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | "Watch Ad & Export" button on mobile Reports tab |
| AC2 | Rewarded video ad plays full screen |
| AC3 | Export unlocked only after ad completion |
| AC4 | If ad skipped/closed early, show message and don't export |
| AC5 | Fallback: if offline or ad fails to load, allow export without ad |
| AC6 | Desktop shows regular "Export" button (no ad) |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Ad completion correctly triggers export |
| IV2 | Offline fallback works reliably |
| IV3 | User informed clearly about ad requirement |

---

## Epic 4: Polish - UX Improvements

**Epic Goal:** Enhance user experience with quality-of-life improvements to the monitoring interface.

**Integration Requirements:**
- Must not disrupt existing functionality
- Visual changes must respect theme system

---

### Story 4.1: Add Monitoring Duration Display

> **As a** user,
> **I want** to see how long I've been monitoring,
> **so that** I know the extent of my current monitoring session.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Card displays "Monitoring: Xh Xm Xs" when active |
| AC2 | Timer updates every second |
| AC3 | Timer resets when monitoring stopped/started |
| AC4 | Card hidden when monitoring is stopped |
| AC5 | Positioned at top of Monitor tab, below header |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Timer accurate to within 1 second |
| IV2 | Timer doesn't cause memory leaks |
| IV3 | Card respects dark/light theme |

---

### Story 4.2: Add Data Retention Configuration

> **As a** user,
> **I want** to configure how long data is retained,
> **so that** I can balance storage usage with data availability.

#### Acceptance Criteria
| # | Criteria |
|---|----------|
| AC1 | Retention period setting in Settings tab (days) |
| AC2 | Options: 7, 14, 30, 60, 90 days |
| AC3 | Default: 30 days |
| AC4 | Change triggers immediate cleanup of expired data |
| AC5 | Confirmation dialog if reducing retention will delete data |

#### Integration Verification
| # | Verification |
|---|--------------|
| IV1 | Cleanup respects new retention setting |
| IV2 | Setting persists across app restarts |
| IV3 | Reports statistics updated after cleanup |

---

## 7. Story Sequence Summary

| Order | Story | Dependencies | Risk Level |
|-------|-------|--------------|------------|
| **1.0** | **Regression Test Suite** | **None (PREREQUISITE)** | **Low** |
| 1.1 | Database Service Layer | 1.0 | Low |
| 1.2 | Schema & Migrations | 1.1 | Low |
| 1.3 | Ping Persistence | 1.1, 1.2 | Medium |
| 1.4 | Tab Navigation | 1.0 (parallel with 1.1-1.3) | Medium |
| 1.5 | Data Retention | 1.2 | Low |
| 2.1 | Settings Service | 1.2 | Low |
| 2.2 | Monitoring Config | 2.1 | Low |
| 2.3 | Region Selection | 2.1 | Low |
| 2.4 | User Info Form | 2.1, 2.3 | Low |
| 2.5 | Connection Info Form | 2.1 | Low |
| 2.6 | Geolocation | 2.4 | Low |
| 3.1 | Reports Statistics | 1.3 | Low |
| 3.2 | Outage Detection | 1.3, 3.1 | Medium |
| 3.3 | IP Tracking | 3.2 | Low |
| 3.4 | Data Clear | 3.1 | Low |
| 3.5 | JSON Export | 3.1, 2.1 | Low |
| 3.6 | Prompt Export | 3.5 | Low |
| 3.7 | Banner Ads | 1.4 | Low |
| 3.8 | Rewarded Ad Export | 3.5, 3.7 | Medium |
| 4.1 | Monitoring Duration | 1.4 | Low |
| 4.2 | Retention Config | 1.5, 2.1 | Low |

---

## Appendix A: Reference Documents

- [POST-MVP-ROADMAP.md](./references/POST-MVP-ROADMAP.md) - Original feature specification
- [RELEASE_PROCESS.md](./references/RELEASE_PROCESS.md) - Release and deployment procedures
- [README.md](../README.md) - Project overview and setup instructions
