import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HomePage } from './home.page';
import { MonitorService } from '../services/monitor.service';
import { BehaviorSubject } from 'rxjs';
import { PingResult } from '../models/ping-result.interface';
import { BaseChartDirective } from 'ng2-charts';
import { IonicModule } from '@ionic/angular';

describe('HomePage', () => {
    let component: HomePage;
    let fixture: ComponentFixture<HomePage>;
    let monitorServiceSpy: Partial<MonitorService>;
    let resultsSubject: BehaviorSubject<PingResult[]>;

    beforeEach(async () => {
        resultsSubject = new BehaviorSubject<PingResult[]>([]);
        monitorServiceSpy = {
            startMonitoring: vi.fn().mockName("MonitorService.startMonitoring"),
            stopMonitoring: vi.fn().mockName("MonitorService.stopMonitoring"),
            results$: resultsSubject.asObservable()
        };

        await TestBed.configureTestingModule({
            imports: [HomePage, IonicModule.forRoot(), BaseChartDirective],
            providers: [
                { provide: MonitorService, useValue: monitorServiceSpy }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(HomePage);
        component = fixture.componentInstance;
    });

    describe('General Functionality', () => {
        beforeEach(() => {
            // Default setup for general tests
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

        it('should call startMonitoring when button clicked', () => {
            component.isMonitoring = false;
            component.toggleMonitoring();
            expect(monitorServiceSpy.startMonitoring).toHaveBeenCalled();
            expect(component.isMonitoring).toBe(true);
        });

        it('should call stopMonitoring when button clicked if already monitoring', () => {
            component.isMonitoring = true;
            component.toggleMonitoring();
            expect(monitorServiceSpy.stopMonitoring).toHaveBeenCalled();
            expect(component.isMonitoring).toBe(false);
        });
    });

    // RT-005: Should calculate average latency correctly
    describe('RT-005: Average latency calculation', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('should calculate average latency correctly', () => {
            const mockResults: PingResult[] = [
                { timestamp: new Date(), latencyMs: 10, status: 'ok' },
                { timestamp: new Date(), latencyMs: 20, status: 'ok' },
                { timestamp: new Date(), latencyMs: 30, status: 'ok' }
            ];
            resultsSubject.next(mockResults);

            expect(component.stats.avg).toBe(20);
        });
    });

    // RT-006: Should calculate min/max latency correctly
    describe('RT-006: Min/max latency calculation', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('should calculate min/max latency correctly', () => {
            const mockResults: PingResult[] = [
                { timestamp: new Date(), latencyMs: 10, status: 'ok' },
                { timestamp: new Date(), latencyMs: 50, status: 'ok' },
                { timestamp: new Date(), latencyMs: 30, status: 'ok' }
            ];
            resultsSubject.next(mockResults);

            expect(component.stats.min).toBe(10);
            expect(component.stats.max).toBe(50);
            expect(component.stats.current).toBe(30); // Last value
        });
    });

    // RT-007: Should calculate jitter with exponential smoothing
    describe('RT-007: Jitter calculation with exponential smoothing', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('should calculate jitter with exponential smoothing (factor 1/16)', () => {
            const mockResults: PingResult[] = [
                { timestamp: new Date(), latencyMs: 10, status: 'ok' },
                { timestamp: new Date(), latencyMs: 20, status: 'ok' },
                { timestamp: new Date(), latencyMs: 10, status: 'ok' }
            ];

            resultsSubject.next(mockResults);
            // Jitter calculation: diff1=10, jitter1=10/16=0.625; diff2=10, jitter2=0.625+(10-0.625)/16=1.2109375
            expect(component.stats.jitter).toBeCloseTo(1.2109375, 4);
        });

        it('should return 0 jitter for single result', () => {
            const mockResults: PingResult[] = [
                { timestamp: new Date(), latencyMs: 50, status: 'ok' }
            ];

            resultsSubject.next(mockResults);
            expect(component.stats.jitter).toBe(0);
        });
    });

    // RT-008: Should filter error results from statistics
    describe('RT-008: Filter error results from statistics', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('should exclude error results from statistics calculations', () => {
            const mockResults: PingResult[] = [
                { timestamp: new Date(), latencyMs: 10, status: 'ok' },
                { timestamp: new Date(), latencyMs: null, status: 'error' },
                { timestamp: new Date(), latencyMs: 30, status: 'ok' },
                { timestamp: new Date(), latencyMs: null, status: 'error' }
            ];
            resultsSubject.next(mockResults);

            // Should only consider the two 'ok' results (10 and 30)
            expect(component.stats.avg).toBe(20);
            expect(component.stats.min).toBe(10);
            expect(component.stats.max).toBe(30);
            expect(component.stats.current).toBe(30);
        });

        it('should reset stats to zero when all results are errors', () => {
            const mockResults: PingResult[] = [
                { timestamp: new Date(), latencyMs: null, status: 'error' },
                { timestamp: new Date(), latencyMs: null, status: 'error' }
            ];
            resultsSubject.next(mockResults);

            expect(component.stats).toEqual({
                current: 0,
                avg: 0,
                min: 0,
                max: 0,
                jitter: 0
            });
        });
    });

    // RT-009: Should update chart data on new results
    describe('RT-009: Chart data updates', () => {
        beforeEach(() => {
            fixture.detectChanges();
        });

        it('should update chart labels and data when results are emitted', () => {
            const now = new Date();
            const mockResults: PingResult[] = [
                { timestamp: now, latencyMs: 25, status: 'ok' },
                { timestamp: new Date(now.getTime() + 1000), latencyMs: 35, status: 'ok' }
            ];
            resultsSubject.next(mockResults);

            expect(component.lineChartData.labels?.length).toBe(2);
            expect(component.lineChartData.datasets[0].data).toEqual([25, 35]);
        });

        it('should display 0 for error results in chart', () => {
            const now = new Date();
            const mockResults: PingResult[] = [
                { timestamp: now, latencyMs: 25, status: 'ok' },
                { timestamp: new Date(now.getTime() + 1000), latencyMs: null, status: 'error' }
            ];
            resultsSubject.next(mockResults);

            expect(component.lineChartData.datasets[0].data).toEqual([25, 0]);
        });
    });

    // NOTE: Theme tests (RT-010, RT-011, RT-012) moved to tabs.page.spec.ts
    // Theme management was relocated from HomePage to TabsPage as part of the
    // design change: tabs moved from bottom bar to top toolbar with shared header.
});
