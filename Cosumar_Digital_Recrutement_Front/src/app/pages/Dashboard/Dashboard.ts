import { Component, signal, OnInit, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'Dashboard',
  standalone: true,
  imports: [],
  templateUrl: './Dashboard.html',
  styleUrl: './Dashboard.css'
})
export class Dashboard implements OnInit {
  private http = inject(HttpClient);

  // Dashboard data - now dynamic
  totalPostes = signal('--');
  totalCandidatures = signal('--');
  totalUtilisateurs = signal('--');
  pendingCandidatures = signal('--');
  
  // Loading state
  isLoading = signal(true);
  isMobile: boolean = false;
  
  ngOnInit(): void {
    this.isMobile = window.innerWidth < 768;
    this.loadDashboardStats();
  }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  loadDashboardStats(): void {
    this.isLoading.set(true);
    
    this.http.get<any>(`${environment.apiUrl}dashboard/stats/`, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (data) => {
        this.totalPostes.set(data.active_postes.toString());
        this.totalCandidatures.set(data.total_candidatures.toString());
        this.totalUtilisateurs.set(data.active_users.toString());
        this.pendingCandidatures.set(data.pending_candidatures.toString());
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error loading dashboard stats:', error);
        // Keep placeholder values on error
        this.totalPostes.set('N/A');
        this.totalCandidatures.set('N/A');
        this.totalUtilisateurs.set('N/A');
        this.pendingCandidatures.set('N/A');
        this.isLoading.set(false);
      }
    });
  }
}
