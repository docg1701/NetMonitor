# 4. Technical Constraints and Integration Requirements

## 4.1 Existing Technology Stack

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

## 4.2 Integration Approach

### Database Integration Strategy

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

### API Integration Strategy

| External Service | Purpose | Integration Point |
|------------------|---------|-------------------|
| `ipify.org` | Public IP lookup | New `IpService` - called on app start + after detected reconnection |
| `navigator.geolocation` | GPS coordinates | Capacitor Geolocation plugin - requested once in Settings |
| AdMob | Monetization | `AdService` - mobile-only, initialized on app start |

**No backend API** - all data stays local. External calls are read-only lookups.

### Frontend Integration Strategy

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

### Testing Integration Strategy

| Test Type | Tool | Focus |
|-----------|------|-------|
| Unit Tests | Vitest | Services, components |
| E2E Tests | None currently | Consider adding Playwright for tab navigation |
| Manual Testing | Device testing | Platform-specific features (SQLite, AdMob) |

**Constraint:** SQLite and AdMob require device/emulator testing - cannot be fully tested in browser.

---

## 4.3 Code Organization and Standards

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

## 4.4 Deployment and Operations

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

## 4.5 Risk Assessment and Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQLite plugin incompatibility between Tauri/Capacitor | Medium | High | Use abstract service layer; test both platforms early |
| AdMob initialization failures on older devices | Low | Medium | Graceful fallback - allow export without ad if ad fails |
| Geolocation permission denied | Medium | Low | Make GPS optional; app works without it |
| Large database size over time | Medium | Medium | Implement auto-cleanup; data retention settings |

### Integration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing Monitor functionality during refactor | Medium | High | Refactor incrementally; keep existing service interfaces |
| Theme inconsistency in new tabs | Low | Medium | Reuse existing CSS variables; test both themes |
| Tab navigation breaking deep links | Low | Low | No deep links currently; not a concern |

### Deployment Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration failures on existing installations | Low | High | Version migrations carefully; test upgrade path |
| App store rejection due to AdMob compliance | Low | Medium | Follow AdMob policies strictly; proper consent flows |

### Mitigation Strategies

1. **Incremental Development**: Implement Phase 1 (SQLite) first, validate on both platforms before proceeding
2. **Feature Flags**: Consider environment-based flags for mobile-only features (ads)
3. **Database Versioning**: Use migration system from day one, even for initial schema
4. **Platform Abstraction**: All platform-specific code behind interfaces for easy testing/mocking

---
