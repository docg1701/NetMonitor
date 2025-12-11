import { inject, Injectable } from '@angular/core';
import { Observable, from, of, timer, BehaviorSubject, Subscription } from 'rxjs';
import { switchMap, map, catchError } from 'rxjs/operators';
import { TauriService } from './tauri.service';
import { environment } from '../../environments/environment';
import { Capacitor, CapacitorHttp } from '@capacitor/core';
import { PingResult } from '../models/ping-result.interface';

@Injectable({
  providedIn: 'root'
})
export class MonitorService {
  private readonly tauriService = inject(TauriService);
  private readonly pingUrl = environment.pingUrl || 'https://www.google.com';
  private pollingSubscription: Subscription | null = null;
  private _results$ = new BehaviorSubject<PingResult[]>([]);

  readonly results$ = this._results$.asObservable();

  startMonitoring(intervalMs: number = 2000): void {
    this.stopMonitoring(); // Ensure no duplicate subscriptions

    this.pollingSubscription = timer(0, intervalMs).pipe(
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
    });
  }

  stopMonitoring(): void {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
  }

  private measureLatency(): Observable<PingResult> {
    if (this.isTauri()) {
      return from(this.tauriService.invoke<{ latency_ms: number }>('ping', { url: this.pingUrl })).pipe(
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
                url: this.pingUrl
            });
        } else {
            // Standard Fetch for Web (Development) - might hit CORS if not proxied
            await fetch(this.pingUrl, { method: 'HEAD', mode: 'no-cors' }); 
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

