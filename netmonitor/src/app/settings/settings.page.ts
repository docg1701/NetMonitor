import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule, ToastController } from '@ionic/angular';
import { Subscription } from 'rxjs';

import { SettingsService } from '../services/settings.service';
import { DEFAULT_SETTINGS } from '../models/settings.interface';
import { PING_TARGET_OPTIONS, PingTargetOption } from '../models/ping-targets.constant';

@Component({
  selector: 'app-settings',
  templateUrl: 'settings.page.html',
  styleUrls: ['settings.page.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, IonicModule]
})
export class SettingsPage implements OnInit, OnDestroy {
  private readonly settingsService = inject(SettingsService);
  private readonly toastController = inject(ToastController);
  private readonly cd = inject(ChangeDetectorRef);

  private subscription: Subscription | null = null;

  /** Ping target dropdown options */
  pingTargetOptions: PingTargetOption[] = PING_TARGET_OPTIONS;

  /** Currently selected ping target */
  selectedTarget = '';

  /** Current ping interval in seconds */
  pingInterval = 5;

  ngOnInit(): void {
    this.subscription = this.settingsService.settings$.subscribe(settings => {
      this.selectedTarget = settings.monitoringConfig.pingTarget;
      this.pingInterval = settings.monitoringConfig.pingInterval;
      this.cd.detectChanges();
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  /**
   * Handle ping target selection change.
   * Saves new target to settings immediately.
   */
  async onTargetChange(value: string): Promise<void> {
    await this.settingsService.updateMonitoringConfig({ pingTarget: value });
    await this.showSavedToast();
  }

  /**
   * Handle ping interval change with validation.
   * Clamps value to 1-60 range before saving.
   */
  async onIntervalChange(value: number): Promise<void> {
    // Clamp to valid range (1-60 seconds)
    const clamped = Math.max(1, Math.min(60, value));

    // Update local state if value was clamped
    if (clamped !== value) {
      this.pingInterval = clamped;
    }

    await this.settingsService.updateMonitoringConfig({ pingInterval: clamped });
    await this.showSavedToast();
  }

  /**
   * Restore monitoring settings to defaults.
   */
  async restoreDefaults(): Promise<void> {
    await this.settingsService.updateMonitoringConfig(DEFAULT_SETTINGS.monitoringConfig);
    await this.showToast('Defaults restored', 'medium');
  }

  /**
   * Show a success toast notification for settings saved.
   */
  private async showSavedToast(): Promise<void> {
    await this.showToast('Settings saved', 'success');
  }

  /**
   * Create and display a toast notification.
   */
  private async showToast(message: string, color: string): Promise<void> {
    const toast = await this.toastController.create({
      message,
      duration: 1500,
      position: 'bottom',
      color,
      cssClass: 'auto-width-toast'
    });
    await toast.present();
  }
}
