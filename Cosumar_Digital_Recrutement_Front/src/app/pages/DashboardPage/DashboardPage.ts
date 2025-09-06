import { Component, EventEmitter, Output, HostListener, OnInit, OnDestroy, inject } from '@angular/core';
import { Router, RouterOutlet, RouterLink, NavigationEnd } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { signal } from '@angular/core';
import { filter } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  templateUrl: './DashboardPage.html',
  styleUrl: './DashboardPage.css'
})
export class DashboardPage implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  
  // User information
  userName = signal((localStorage.getItem('prenom') || '') + ' ' + (localStorage.getItem('nom') || '') || 'Utilisateur');
  userRole = signal(localStorage.getItem('role') || 'Utilisateur');
  userEmail = signal(localStorage.getItem('email') || 'Utilisateur');

  // UI state
  activeMenuItem = signal('dashboard');
  isUserMenuOpen = signal(false);
  isSidebarCollapsed = signal(true);
  notificationCount = signal(5);
  isMobile = false;
  
  @Output() logoutRequest = new EventEmitter<void>();
  @Output() profileView = new EventEmitter<void>();
  @Output() profileEdit = new EventEmitter<void>();

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.isMobile = window.innerWidth < 768;
    // Set active menu item based on current route
    this.updateActiveMenuFromRoute();
    
    // Listen to route changes
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.updateActiveMenuFromRoute();
    });
  }

  ngOnDestroy(): void {
    // Component cleanup
  }

  private updateActiveMenuFromRoute(): void {
    const currentRoute = this.router.url;
    if (currentRoute.includes('creationstage')) {
      this.activeMenuItem.set('creation_stage');
    } else if (currentRoute.includes('stages')) {
      this.activeMenuItem.set('stages');
    } else if (currentRoute.includes('stagiaires')) {
      this.activeMenuItem.set('stagiaires');
    } else if (currentRoute.includes('candidats')) {
      this.activeMenuItem.set('candidats');
    } else if (currentRoute.includes('utilisateurs')) {
      this.activeMenuItem.set('utilisateurs');
    } else if (currentRoute.includes('domaines')) {
      this.activeMenuItem.set('domaines');
    } else if (currentRoute.includes('profile')) {
      this.activeMenuItem.set('profile');
    } else {
      this.activeMenuItem.set('dashboard');
    }
  }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  setActiveMenuItem(item: string): void {
    this.activeMenuItem.set(item);
    this.closeUserMenu();
  }

  toggleUserMenu(): void {
    this.isUserMenuOpen.update(value => !value);
  }

  closeUserMenu(): void {
    this.isUserMenuOpen.set(false);
  }

  toggleSidebar(): void {
    this.isSidebarCollapsed.update(value => !value);
    this.closeUserMenu();
    console.log('Sidebar collapsed:', this.isSidebarCollapsed); // Debug log
  }

  getPageTitle(): string {
    const titles: { [key: string]: string } = {
      'dashboard': 'Tableau de bord',
      'creation_stage': 'Création de Stage',
      'stages': 'Gestion des Stages',
      'stagiaires': 'Liste des Stagiaires',
      'candidats': 'Gestion des Candidats',
      'utilisateurs': 'Gestion des Utilisateurs',
      'domaines': 'Gestion des Domaines',
      'profile': 'Mon Profil'
    };
    return titles[this.activeMenuItem()] || 'Tableau de bord';
  }

  viewProfile(): void {
    this.closeUserMenu();
    this.router.navigate(['/dashboardpage/profile']);
  }

  editProfile(): void {
    this.closeUserMenu();
    this.profileEdit.emit();
  }

  accountSettings(): void {
    this.closeUserMenu();
    // Navigate to account settings
    console.log('Navigate to account settings');
  }

  logout(): void {
    this.closeUserMenu();
    localStorage.clear();
    this.router.navigate(['/login'], { replaceUrl: true });
  }

  // Close user menu when clicking outside
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.user-menu')) {
      this.closeUserMenu();
    }
  }

  @HostListener('window:resize', ['$event'])
  onResize(event: any): void {
    this.isMobile = event.target.innerWidth < 768;
    if (this.isMobile) {
      this.isSidebarCollapsed.set(false); // Reset collapse state on mobile
    }
  }
}