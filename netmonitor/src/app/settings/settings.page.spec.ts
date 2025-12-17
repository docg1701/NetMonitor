import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SettingsPage } from './settings.page';
import { IonicModule } from '@ionic/angular';
import { describe, it, expect, beforeEach } from 'vitest';

describe('SettingsPage', () => {
  let component: SettingsPage;
  let fixture: ComponentFixture<SettingsPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsPage, IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have placeholder content', () => {
    // Note: Header with title is now in TabsPage (shared header)
    const compiled = fixture.nativeElement;
    const content = compiled.querySelector('ion-content');
    expect(content.textContent).toContain('Coming soon');
  });
});
