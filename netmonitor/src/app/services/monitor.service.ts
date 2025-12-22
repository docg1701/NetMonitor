import { inject, Injectable } from '@angular/core';
import { Observable, from, of, timer, BehaviorSubject, Subscription } from 'rxjs';
import { switchMap, map, catchError } from 'rxjs/operators';
import { TauriService } from './tauri.service';
import { Capacitor, CapacitorHttp } from '@capacitor/core';
import { PingResult } from '../models/ping-result.interface';
import { PingRepository } from './ping.repository';
import { SettingsService } from './settings.service';

@Injectable({
  providedIn: 'root'
})
export class MonitorService {
  private readonly tauriService = inject(TauriService);
  private readonly pingRepository = inject(PingRepository);
  private readonly settingsService = inject(SettingsService);
  private pollingSubscription: Subscription | null = null;
  private _results$ = new BehaviorSubject<PingResult[]>([]);
  private _isMonitoring$ = new BehaviorSubject<boolean>(false);

  readonly results$ = this._results$.asObservable();
  readonly isMonitoring$ = this._isMonitoring$.asObservable();

  /**
   * Get current ping target from settings.
   */
  private get pingTarget(): string {
    return this.settingsService.getCurrentSettings().monitoringConfig.pingTarget;
  }

  /**
   * Get current ping interval in milliseconds from settings.
   * Settings store interval in seconds, this converts to ms.
   */
  private get pingIntervalMs(): number {
    return this.settingsService.getCurrentSettings().monitoringConfig.pingInterval * 1000;
  }

  startMonitoring(intervalMs?: number): void {
    this.stopMonitoring(); // Ensure no duplicate subscriptions
    this._isMonitoring$.next(true);

    const interval = intervalMs ?? this.pingIntervalMs;
    this.pollingSubscription = timer(0, interval).pipe(
      switchMap(() => this.measureLatency()),
      catchError(err => {
        console.error('Monitoring error:', err);
        return of({ latencyMs: null, timestamp: new Date(), status: 'error' } as PingResult);
      })
    ).subscribe(result => {
        const current = this._results$.value;
        // Keep last 50 points
        const updated = [...current, result].slice(-50);
        this._results$.next(updated);
        // Persist to database (fire-and-forget, non-blocking)
        this.pingRepository.savePing(result, this.pingTarget);
    });
  }

  stopMonitoring(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
    this._isMonitoring$.next(false);
  }

  private measureLatency(): Observable<PingResult> {
    if (this.isTauri()) {
      return from(this.tauriService.invoke<{ latency_ms: number }>('ping', { url: this.pingTarget })).pipe(
        map(res => ({
          latencyMs: res.latency_ms,
          timestamp: new Date(),
          status: 'ok'
        } as PingResult)),
        catchError(err => {
            console.error('Tauri ping error:', err);
            return of({ latencyMs: null, timestamp: new Date(), status: 'error' } as PingResult);
        })
      );
    } else {
      // Fallback for Web/Mobile (Capacitor)
      return from(this.measureWebLatency()).pipe(
          catchError(err => {
              console.error('Web/Capacitor ping error:', err);
              return of({ latencyMs: null, timestamp: new Date(), status: 'error' } as PingResult);
          })
      );
    }
  }

  private async measureWebLatency(): Promise<PingResult> {
    const start = Date.now();
    try {
        // Use CapacitorHttp for better CORS handling on devices
        if (Capacitor.isNativePlatform()) {
            await CapacitorHttp.request({
                method: 'HEAD',
                url: this.pingTarget
            });
        } else {
            // Standard Fetch for Web (Development) - might hit CORS if not proxied
            await fetch(this.pingTarget, { method: 'HEAD', mode: 'no-cors' });
        }
        const end = Date.now();
        return {
            latencyMs: end - start,
            timestamp: new Date(),
            status: 'ok'
        };
    } catch (error) {
        console.error('Latency measurement failed', error);
        throw error;
    }
  }

  private isTauri(): boolean {
    return !!(window as any).__TAURI__;
  }
}

