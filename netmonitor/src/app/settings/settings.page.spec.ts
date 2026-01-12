import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SettingsPage } from './settings.page';
import { SettingsService } from '../services/settings.service';
import { IonicModule, ToastController } from '@ionic/angular';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BehaviorSubject } from 'rxjs';
import { AppSettings, DEFAULT_SETTINGS } from '../models/settings.interface';
import { PING_TARGET_OPTIONS } from '../models/ping-targets.constant';

describe('SettingsPage', () => {
  let component: SettingsPage;
  let fixture: ComponentFixture<SettingsPage>;
  let mockSettingsService: {
    settings$: BehaviorSubject<AppSettings>;
    updateMonitoringConfig: ReturnType<typeof vi.fn>;
  };
  let mockToastController: {
    create: ReturnType<typeof vi.fn>;
  };
  let mockToast: { present: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    mockSettingsService = {
      settings$: new BehaviorSubject<AppSettings>(DEFAULT_SETTINGS),
      updateMonitoringConfig: vi.fn().mockResolvedValue(undefined)
    };

    mockToast = { present: vi.fn().mockResolvedValue(undefined) };
    mockToastController = {
      create: vi.fn().mockResolvedValue(mockToast)
    };

    await TestBed.configureTestingModule({
      imports: [SettingsPage, IonicModule.forRoot()],
      providers: [
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: ToastController, useValue: mockToastController }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with settings from SettingsService', () => {
    expect(component.selectedTarget).toBe('8.8.8.8');
    expect(component.pingInterval).toBe(5);
  });

  it('should have all ping target options available', () => {
    expect(component.pingTargetOptions).toEqual(PING_TARGET_OPTIONS);
    expect(component.pingTargetOptions.length).toBe(6);
  });

  it('should update settings when target changes', async () => {
    await component.onTargetChange('1.1.1.1');

    expect(mockSettingsService.updateMonitoringConfig).toHaveBeenCalledWith({
      pingTarget: '1.1.1.1'
    });
  });

  it('should show toast when target changes', async () => {
    await component.onTargetChange('1.1.1.1');

    expect(mockToastController.create).toHaveBeenCalledWith({
      message: 'Settings saved',
      duration: 1500,
      position: 'bottom',
      color: 'success',
      cssClass: 'auto-width-toast'
    });
    expect(mockToast.present).toHaveBeenCalled();
  });

  it('should update settings when interval changes', async () => {
    await component.onIntervalChange(10);

    expect(mockSettingsService.updateMonitoringConfig).toHaveBeenCalledWith({
      pingInterval: 10
    });
  });

  it('should clamp interval to minimum of 1', async () => {
    await component.onIntervalChange(0);

    expect(mockSettingsService.updateMonitoringConfig).toHaveBeenCalledWith({
      pingInterval: 1
    });
    expect(component.pingInterval).toBe(1);
  });

  it('should clamp interval to maximum of 60', async () => {
    await component.onIntervalChange(100);

    expect(mockSettingsService.updateMonitoringConfig).toHaveBeenCalledWith({
      pingInterval: 60
    });
    expect(component.pingInterval).toBe(60);
  });

  it('should show toast when interval changes', async () => {
    await component.onIntervalChange(10);

    expect(mockToastController.create).toHaveBeenCalledWith({
      message: 'Settings saved',
      duration: 1500,
      position: 'bottom',
      color: 'success',
      cssClass: 'auto-width-toast'
    });
    expect(mockToast.present).toHaveBeenCalled();
  });

  it('should restore defaults when restoreDefaults is called', async () => {
    await component.restoreDefaults();

    expect(mockSettingsService.updateMonitoringConfig).toHaveBeenCalledWith(
      DEFAULT_SETTINGS.monitoringConfig
    );
  });

  it('should show toast with "Defaults restored" when restoring defaults', async () => {
    await component.restoreDefaults();

    expect(mockToastController.create).toHaveBeenCalledWith({
      message: 'Defaults restored',
      duration: 1500,
      position: 'bottom',
      color: 'medium',
      cssClass: 'auto-width-toast'
    });
    expect(mockToast.present).toHaveBeenCalled();
  });

  it('should update local state when settings change', () => {
    const newSettings: AppSettings = {
      ...DEFAULT_SETTINGS,
      monitoringConfig: {
        pingTarget: 'www.cloudflare.com',
        pingInterval: 15
      }
    };

    mockSettingsService.settings$.next(newSettings);

    expect(component.selectedTarget).toBe('www.cloudflare.com');
    expect(component.pingInterval).toBe(15);
  });

  it('should unsubscribe on destroy', () => {
    const subscription = (component as unknown as { subscription: { unsubscribe: () => void } }).subscription;
    const unsubscribeSpy = vi.spyOn(subscription, 'unsubscribe');

    component.ngOnDestroy();

    expect(unsubscribeSpy).toHaveBeenCalled();
  });

  it('should render ping target dropdown', () => {
    const compiled = fixture.nativeElement;
    const select = compiled.querySelector('ion-select');
    expect(select).toBeTruthy();
    expect(select.getAttribute('label')).toBe('Ping Target');
  });

  it('should render ping interval input', () => {
    const compiled = fixture.nativeElement;
    const input = compiled.querySelector('ion-input');
    expect(input).toBeTruthy();
    expect(input.getAttribute('label')).toBe('Ping Interval (seconds)');
    expect(input.getAttribute('type')).toBe('number');
  });

  it('should render restore defaults button', () => {
    const compiled = fixture.nativeElement;
    const button = compiled.querySelector('ion-button');
    expect(button).toBeTruthy();
    expect(button.textContent).toContain('Restore Defaults');
  });

  it('should render interval validation note', () => {
    const compiled = fixture.nativeElement;
    const note = compiled.querySelector('ion-note');
    expect(note).toBeTruthy();
    expect(note.textContent).toContain('Valid range: 1-60 seconds');
  });
});
