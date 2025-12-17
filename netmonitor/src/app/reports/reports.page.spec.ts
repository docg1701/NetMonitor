import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReportsPage } from './reports.page';
import { IonicModule } from '@ionic/angular';
import { describe, it, expect, beforeEach } from 'vitest';

describe('ReportsPage', () => {
  let component: ReportsPage;
  let fixture: ComponentFixture<ReportsPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportsPage, IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(ReportsPage);
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
