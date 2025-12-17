import { Routes } from '@angular/router';
import { TabsPage } from './tabs.page';

export const tabsRoutes: Routes = [
  {
    path: '',
    component: TabsPage,
    children: [
      {
        path: 'monitor',
        loadComponent: () => import('../home/home.page').then(m => m.HomePage)
      },
      {
        path: 'settings',
        loadComponent: () => import('../settings/settings.page').then(m => m.SettingsPage)
      },
      {
        path: 'reports',
        loadComponent: () => import('../reports/reports.page').then(m => m.ReportsPage)
      },
      {
        path: '',
        redirectTo: 'monitor',
        pathMatch: 'full'
      }
    ]
  }
];
