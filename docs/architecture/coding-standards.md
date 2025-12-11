# Coding Standards

## Angular/TypeScript Conventions

### Component Pattern

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

### Service Pattern

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

### Platform Detection

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

### Async Operations

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

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Page Component | `{name}.page.ts` | `settings.page.ts` |
| Service | `{name}.service.ts` | `database.service.ts` |
| Interface | `{name}.interface.ts` | `settings.interface.ts` |
| Module | `{name}.module.ts` | `app.module.ts` |
| Routing | `{name}.routes.ts` or `{name}-routing.module.ts` | `tabs.routes.ts` |
| Spec | `{name}.spec.ts` | `monitor.service.spec.ts` |

## CSS/SCSS Conventions

### Use Ionic CSS Custom Properties

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

### Define Custom Properties in variables.scss

```scss
:root {
  --my-custom-color: #3880ff;
}

.ion-palette-dark {
  --my-custom-color: #428cff;
}
```

### Component-Scoped Styles

Keep styles in component `.scss` files, not global:

```scss
// home.page.scss - scoped to HomePage
.chart-container {
  position: relative;
  flex: 1;
}
```

## Rust Conventions (Tauri Backend)

### Command Structure

```rust
#[tauri::command]
async fn my_command(
    arg: String,
    state: State<'_, AppState>
) -> Result<ReturnType, String> {
    // Implementation
}
```

### Error Handling

Return `Result<T, String>` for commands to surface errors to frontend:

```rust
match operation {
    Ok(value) => Ok(value),
    Err(e) => Err(format!("Operation failed: {}", e))
}
```

## Testing Conventions

### Test Requirements

- **Regression tests MUST pass** before any enhancement story is considered complete
- **New features MUST include unit tests** for all public methods
- **Coverage target:** 80% on services and business logic

### Unit Test Structure

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

### Test Naming Convention

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

### Mocking Platform-Specific APIs

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

## Code Quality Rules

1. **No hardcoded strings** - Use constants or environment variables
2. **No `any` type** - Define proper interfaces
3. **No unused imports** - Clean up after refactoring
4. **Document public APIs** - JSDoc for service methods
5. **Handle errors** - Never swallow errors silently
6. **Platform checks** - Always verify platform before native calls

---
