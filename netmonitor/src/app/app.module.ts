import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouteReuseStrategy } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { Capacitor } from '@capacitor/core';

import { IonicModule, IonicRouteStrategy } from '@ionic/angular';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { DatabaseService } from './services/database.service';
import { TauriDatabaseService } from './services/tauri-database.service';
import { CapacitorDatabaseService } from './services/capacitor-database.service';
import { WebDatabaseService } from './services/web-database.service';

export function databaseServiceFactory(): DatabaseService {
  if ((window as unknown as { __TAURI__?: unknown }).__TAURI__) {
    return new TauriDatabaseService();
  } else if (Capacitor.isNativePlatform()) {
    return new CapacitorDatabaseService();
  } else {
    return new WebDatabaseService();
  }
}

@NgModule({
  imports: [BrowserModule, IonicModule.forRoot(), AppRoutingModule, AppComponent],
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideHttpClient(withInterceptorsFromDi()),
    { provide: DatabaseService, useFactory: databaseServiceFactory }
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
