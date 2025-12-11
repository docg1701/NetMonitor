# Testing Strategy

## Current Test Coverage

| Type | Tool | Coverage | Files |
|------|------|----------|-------|
| Unit Tests | Vitest | 80%+ | `*.spec.ts` files with comprehensive coverage |
| Integration | None | 0% | - |
| E2E | None | 0% | - |

## Required: Regression Test Suite (Story 1.0)

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

## Running Tests

```bash
npm test                    # Runs unit tests with Vitest in Chromium browser
npx ng test --coverage      # With coverage report
```

## Test Files

| File | Purpose |
|------|---------|
| `app.component.spec.ts` | Root component smoke test |
| `home.page.spec.ts` | Monitor page tests (to be expanded) |
| `monitor.service.spec.ts` | Core service tests (to be expanded) |

**Note:** SQLite and AdMob features will require device/emulator testing - cannot be unit tested in browser.

---
