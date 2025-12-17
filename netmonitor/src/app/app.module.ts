import { NgModule, APP_INITIALIZER } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouteReuseStrategy } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { Capacitor } from '@capacitor/core';
import { isTauri } from '@tauri-apps/api/core';
import { firstValueFrom } from 'rxjs';
import { filter } from 'rxjs/operators';

import { IonicModule, IonicRouteStrategy } from '@ionic/angular';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { DatabaseService } from './services/database.service';
import { TauriDatabaseService } from './services/tauri-database.service';
import { CapacitorDatabaseService } from './services/capacitor-database.service';
import { WebDatabaseService } from './services/web-database.service';
import { MigrationService } from './services/migration.service';
import { createV1Migration } from './services/migrations/v1-initial-schema';
import { CleanupService } from './services/cleanup.service';

export function databaseServiceFactory(): DatabaseService {
  if (isTauri()) {
    console.log('DatabaseFactory: Tauri detected, using TauriDatabaseService');
    return new TauriDatabaseService();
  } else if (Capacitor.isNativePlatform()) {
    console.log('DatabaseFactory: Capacitor detected, using CapacitorDatabaseService');
    return new CapacitorDatabaseService();
  } else {
    console.log('DatabaseFactory: Browser detected, using WebDatabaseService');
    return new WebDatabaseService();
  }
}

export function initializeMigrations(
  db: DatabaseService,
  migrationService: MigrationService,
  cleanupService: CleanupService
): () => Promise<void> {
  return async () => {
    console.log('APP_INIT: Starting database initialization...');

    try {
      // Initialize the database connection first
      await db.init();
      console.log('APP_INIT: db.init() completed, isInitialized:', db.isInitialized);
    } catch (e) {
      console.error('APP_INIT: db.init() failed:', e);
      return; // Don't block app startup
    }

    // Skip waiting if already initialized
    if (!db.isInitialized) {
      console.log('APP_INIT: Waiting for isInitialized$...');
      await firstValueFrom(db.isInitialized$.pipe(filter(ready => ready)));
    }
    console.log('APP_INIT: Database ready');

    // Register migrations
    migrationService.registerMigration(createV1Migration(db));
    console.log('APP_INIT: Migrations registered');

    // Run pending migrations
    await migrationService.runMigrations();
    console.log('APP_INIT: Migrations complete');

    // Run data retention cleanup
    try {
      await cleanupService.runCleanup();
      console.log('APP_INIT: Cleanup complete');
    } catch (e) {
      console.error('APP_INIT: Cleanup failed:', e);
      // Don't block app startup on cleanup failure
    }
  };
}

@NgModule({
  imports: [BrowserModule, IonicModule.forRoot(), AppRoutingModule, AppComponent],
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideHttpClient(withInterceptorsFromDi()),
    { provide: DatabaseService, useFactory: databaseServiceFactory },
    {
      provide: APP_INITIALIZER,
      useFactory: initializeMigrations,
      deps: [DatabaseService, MigrationService, CleanupService],
      multi: true
    }
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
