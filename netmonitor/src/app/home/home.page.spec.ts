import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HomePage } from './home.page';
import { MonitorService } from '../services/monitor.service';
import { BehaviorSubject, of } from 'rxjs';
import { PingResult } from '../models/ping-result.interface';
import { BaseChartDirective } from 'ng2-charts';
import { IonicModule } from '@ionic/angular';

describe('HomePage', () => {
  let component: HomePage;
  let fixture: ComponentFixture<HomePage>;
  let monitorServiceSpy: jasmine.SpyObj<MonitorService>;
  let resultsSubject: BehaviorSubject<PingResult[]>;

  beforeEach(async () => {
    resultsSubject = new BehaviorSubject<PingResult[]>([]);
    monitorServiceSpy = jasmine.createSpyObj('MonitorService', ['startMonitoring', 'stopMonitoring'], {
      results$: resultsSubject.asObservable()
    });

    await TestBed.configureTestingModule({
      imports: [HomePage, IonicModule.forRoot(), BaseChartDirective], // HomePage is standalone
      providers: [
        { provide: MonitorService, useValue: monitorServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(HomePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have default stats', () => {
    expect(component.stats).toEqual({
      current: 0,
      avg: 0,
      min: 0,
      max: 0,
      jitter: 0
    });
  });

  it('should update stats when results are emitted', () => {
    const mockResults: PingResult[] = [
      { timestamp: new Date(), latencyMs: 10, status: 'ok' },
      { timestamp: new Date(), latencyMs: 20, status: 'ok' },
      { timestamp: new Date(), latencyMs: 30, status: 'ok' }
    ];
    resultsSubject.next(mockResults);
    
    expect(component.stats.current).toBe(30);
    expect(component.stats.avg).toBe(20);
    expect(component.stats.min).toBe(10);
    expect(component.stats.max).toBe(30);
    // Jitter RFC 1889:
    // 1. |20-10|=10. J=0.625
    // 2. |30-20|=10. J=1.2109375
    expect(component.stats.jitter).toBeCloseTo(1.21, 1);
  });

  it('should calculate jitter correctly', () => {
    const mockResults: PingResult[] = [
        { timestamp: new Date(), latencyMs: 10, status: 'ok' },
        { timestamp: new Date(), latencyMs: 20, status: 'ok' },
        { timestamp: new Date(), latencyMs: 10, status: 'ok' }
      ];
      
      // RFC 1889 Jitter:
      // J1 = (|20-10| - 0)/16 = 0.625
      // J2 = 0.625 + (|10-20| - 0.625)/16 = 0.625 + 9.375/16 = 0.625 + 0.5859375 = 1.2109375

      resultsSubject.next(mockResults);
      expect(component.stats.jitter).toBeCloseTo(1.2109375, 4);
  });

  it('should call startMonitoring when button clicked', () => {
    component.isMonitoring = false;
    component.toggleMonitoring();
    expect(monitorServiceSpy.startMonitoring).toHaveBeenCalled();
    expect(component.isMonitoring).toBeTrue();
  });

  it('should call stopMonitoring when button clicked if already monitoring', () => {
    component.isMonitoring = true;
    component.toggleMonitoring();
    expect(monitorServiceSpy.stopMonitoring).toHaveBeenCalled();
    expect(component.isMonitoring).toBeFalse();
  });
});