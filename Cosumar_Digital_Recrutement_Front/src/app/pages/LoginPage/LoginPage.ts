import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { LoginComponent } from '../../components/LoginComponent/LoginComponent';

@Component({
  standalone: true,
  selector: 'LoginPage',
  templateUrl: './LoginPage.html',
  styleUrls: ['./LoginPage.css'],
  imports: [LoginComponent]
})
export class LoginPage {
  private http = inject(HttpClient);
  private router = inject(Router);

  loginMessage = '';

  handleLogin(credentials: { email: string; mot_de_passe: string }) {
    this.loginMessage = `Logging in as ${credentials.email}...`;

    this.http.post(`${environment.apiUrl}auth/login/`, credentials).subscribe({
      next: (response: any) => {
        this.loginMessage = 'Login successful!';
        localStorage.setItem('access', response.access);
        localStorage.setItem('refresh', response.refresh);
        localStorage.setItem('user_id', response.user.user_id);
        localStorage.setItem('role', response.user.role);
        localStorage.setItem('email', response.user.email);
        localStorage.setItem('prenom', response.user.prenom);
        localStorage.setItem('nom', response.user.nom);

        console.log('Login successful:', response);
        this.router.navigate(['/dashboard'], { replaceUrl: true });
        console.log('Navigation to dashboard successful');
      },
      error: () => {
        this.loginMessage = 'Login failed. Please check your credentials.';
      }
    });
  }
}
