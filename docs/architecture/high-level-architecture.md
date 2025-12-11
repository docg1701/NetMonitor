# High Level Architecture

## Technical Summary

NetMonitor is a **cross-platform network latency monitoring tool** built with:
- **Frontend:** Angular 21 + Ionic 8 (hybrid approach: NgModule root + standalone pages)
- **Desktop Runtime:** Tauri 2.9.x (Rust backend)
- **Mobile Runtime:** Capacitor 7.4.x (native Android/iOS bridges)
- **State Management:** RxJS BehaviorSubject pattern (no NgRx/Redux)

## Tech Stack (Complete Reference)

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Angular | 21.0.0 | Application framework |
| Ionic | 8.0.0 | UI component library |
| TypeScript | 5.9.x | Language |
| RxJS | 7.8.x | Reactive programming |
| Chart.js | 4.5.1 | Data visualization |
| ng2-charts | 8.0.0 | Angular Chart.js wrapper |

### Desktop Runtime (Tauri)

| Technology | Version | Purpose |
|------------|---------|---------|
| Tauri | 2.9.4 | Desktop app framework |
| Rust | 1.77.2+ | Backend language |
| reqwest | 0.12 | HTTP client (5s timeout) |
| serde | 1.0 | Serialization |
| tauri-plugin-log | 2.x | Logging |
| tauri-plugin-shell | 2.x | Shell commands |
| tauri-plugin-store | 2.x | Key-value storage |

### Mobile Runtime (Capacitor)

| Technology | Version | Purpose |
|------------|---------|---------|
| Capacitor | 7.4.4 | Mobile app framework |
| @capacitor/android | 7.4.4 | Android runtime |
| @capacitor/ios | 7.4.4 | iOS runtime |
| @capacitor/app | 7.1.1 | App lifecycle |
| @capacitor/haptics | 7.0.3 | Haptic feedback |
| @capacitor/keyboard | 7.0.4 | Keyboard handling |
| @capacitor/status-bar | 7.0.4 | Status bar control |

### Build Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| Angular CLI | 21.0.0 | Build orchestration |
| Tauri CLI | 2.9.5 | Desktop builds |
| Capacitor CLI | 7.4.4 | Mobile builds |
| ESLint | 9.16.x | Code linting |
| Vitest | 3.x | Test framework & runner |
| Playwright | 1.x | Browser test provider |

### Planned Additions (Post-MVP)

| Technology | Version | Purpose |
|------------|---------|---------|
| tauri-plugin-sql | 2.x | SQLite for desktop |
| @capacitor-community/sqlite | 7.x | SQLite for mobile |
| @capacitor/geolocation | 7.x | GPS coordinates |
| @capacitor-community/admob | 6.x | Mobile ads |

---
