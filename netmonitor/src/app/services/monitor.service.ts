import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, Subscription, timer, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { PingResult } from '../models/ping-result.interface';
import { environment } from '../../environments/environment'; // Import environment

@Injectable({
  providedIn: 'root'
})
export class MonitorService {
  private pingResults$ = new BehaviorSubject<PingResult[]>([]);
  private timerSubscription: Subscription | null = null;
  private http = inject(HttpClient);

  get results$(): Observable<PingResult[]> {
    return this.pingResults$.asObservable();
  }

  measureLatency(url: string): Observable<PingResult> {
    const start = Date.now();
    // Using 'response' observation to get full headers if needed, 
    // though HEAD mostly validates connectivity and server responsiveness.
    return this.http.head(url, { observe: 'response' }).pipe(
      map(() => {
        const duration = Date.now() - start;
        return {
          timestamp: new Date(),
          latencyMs: duration,
          status: 'ok' as const
        };
      }),
      catchError(() => {
        return of({
          timestamp: new Date(),
          latencyMs: null,
          status: 'error' as const
        });
      })
    );
  }

  startMonitoring(intervalMs: number): void { // Removed url parameter
    this.stopMonitoring(); // Ensure no duplicate subscriptions

    this.timerSubscription = timer(0, intervalMs).pipe(
      switchMap(() => this.measureLatency(environment.pingUrl)) // Use pingUrl from environment
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
    // Append new result, then slice to keep only the last 50 elements
    const updatedResults = [...currentResults, result];
    if (updatedResults.length > 50) {
        updatedResults.shift(); // Remove the oldest
    }
    this.pingResults$.next(updatedResults);
  }
}

