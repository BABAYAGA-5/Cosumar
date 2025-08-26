import { Routes } from '@angular/router';
import { LoginPage } from './pages/LoginPage/LoginPage';
import { DashboardPage } from './pages/DashboardPage/DashboardPage';
import { Dashboard } from './pages/Dashboard/Dashboard';
import { CreationStage } from './pages/CreationStage/CreationStage';
import { ConsultationStage } from './pages/ConsultationStage/ConsultationStage';
import { StageDetails } from './pages/StageDetails/StageDetails';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginPage },
  { path: 'dashboardpage',
    component: DashboardPage,
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'creationstage', component: CreationStage },
      { path: 'stages', component: ConsultationStage },
      { path: 'stage/:id', component: StageDetails },
      //{ path: 'utilisateurs', component: Utilisateurs },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  },
  { path: '**', redirectTo: '/login' }
];

