import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subscription, timer, from, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { PingResult } from '../models/ping-result.interface';
import { environment } from '../../environments/environment';
import { invoke } from '@tauri-apps/api/core';

// Define the structure expected from Rust
interface RustPingResult {
  success: boolean;
  latency: number;
}

@Injectable({
  providedIn: 'root'
})
export class MonitorService {
  private pingResults$ = new BehaviorSubject<PingResult[]>([]);
  private timerSubscription: Subscription | null = null;
  // private http = inject(HttpClient); // Not used anymore

  get results$(): Observable<PingResult[]> {
    return this.pingResults$.asObservable();
  }

  measureLatency(url: string): Observable<PingResult> {
    // Wrap the Promise returned by invoke in an Observable
    return from(invoke<RustPingResult>('ping', { url })).pipe(
      map((res) => {
        if (res.success) {
          return {
            timestamp: new Date(),
            latencyMs: res.latency,
            status: 'ok' as const
          };
        } else {
           // Logic for explicit failure reported by backend (e.g. DNS error but handled)
           return {
            timestamp: new Date(),
            latencyMs: null,
            status: 'error' as const
           };
        }
      }),
      catchError((err) => {
        console.error('Tauri ping error:', err);
        return of({
          timestamp: new Date(),
          latencyMs: null,
          status: 'error' as const
        });
      })
    );
  }

  startMonitoring(intervalMs: number): void {
    this.stopMonitoring();

    this.timerSubscription = timer(0, intervalMs).pipe(
      switchMap(() => this.measureLatency(environment.pingUrl))
    ).subscribe(result => {
      this.addResult(result);
    });
  }

  stopMonitoring(): void {
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
      this.timerSubscription = null;
    }
  }

  private addResult(result: PingResult): void {
    const currentResults = this.pingResults$.getValue();
    const updatedResults = [...currentResults, result];
    if (updatedResults.length > 50) {
        updatedResults.shift();
    }
    this.pingResults$.next(updatedResults);
  }
}

