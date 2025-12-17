import { Component, ViewChild, OnInit, OnDestroy, inject } from '@angular/core';
import { IonicModule, IonTabs } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { pulseOutline, settingsOutline, documentTextOutline, sunnyOutline, moonOutline } from 'ionicons/icons';
import { Subscription } from 'rxjs';
import { MonitorService } from '../services/monitor.service';

@Component({
  selector: 'app-tabs',
  templateUrl: 'tabs.page.html',
  styleUrls: ['tabs.page.scss'],
  standalone: true,
  imports: [IonicModule]
})
export class TabsPage implements OnInit, OnDestroy {
  @ViewChild('tabs') tabs!: IonTabs;

  monitorService = inject(MonitorService);
  selectedTab = 'monitor';
  isDark = false;
  isMonitoring = false;

  private themeQuery: MediaQueryList | null = null;
  private themeListener: ((e: MediaQueryListEvent) => void) | null = null;
  private monitoringSubscription: Subscription | null = null;

  constructor() {
    addIcons({ pulseOutline, settingsOutline, documentTextOutline, sunnyOutline, moonOutline });
  }

  ngOnInit() {
    this.initializeTheme();

    // Subscribe to monitoring state changes
    this.monitoringSubscription = this.monitorService.isMonitoring$.subscribe(isMonitoring => {
      this.isMonitoring = isMonitoring;
    });
  }

  ngOnDestroy() {
    if (this.themeQuery && this.themeListener) {
      this.themeQuery.removeEventListener('change', this.themeListener);
    }
    if (this.monitoringSubscription) {
      this.monitoringSubscription.unsubscribe();
    }
  }

  onTabChange(event: CustomEvent) {
    const tab = event.detail.value;
    if (tab && this.tabs) {
      this.tabs.select(tab);
    }
  }

  onTabsDidChange(event: { tab: string }) {
    this.selectedTab = event.tab;
  }

  private initializeTheme() {
    this.themeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    this.themeListener = (e: MediaQueryListEvent) => {
      const savedTheme = localStorage.getItem('netmonitor-theme');
      if (!savedTheme) {
        this.setTheme(e.matches);
      }
    };

    this.themeQuery.addEventListener('change', this.themeListener);

    const savedTheme = localStorage.getItem('netmonitor-theme');
    if (savedTheme) {
      this.setTheme(savedTheme === 'dark');
    } else {
      this.setTheme(this.themeQuery.matches);
    }
  }

  private setTheme(isDark: boolean) {
    this.isDark = isDark;
    if (this.isDark) {
      document.body.classList.add('ion-palette-dark');
    } else {
      document.body.classList.remove('ion-palette-dark');
    }
  }

  toggleTheme() {
    const newIsDark = !this.isDark;
    this.setTheme(newIsDark);
    localStorage.setItem('netmonitor-theme', newIsDark ? 'dark' : 'light');
  }
}
