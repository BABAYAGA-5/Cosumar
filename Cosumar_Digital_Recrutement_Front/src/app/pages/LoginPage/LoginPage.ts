import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { LoginComponent } from '../../components/LoginComponent/LoginComponent';
import { NgModel } from '@angular/forms';

@Component({
  standalone: true,
  selector: 'LoginPage',
  templateUrl: './LoginPage.html',
  styleUrls: ['./LoginPage.css']
})
export class LoginPage {
  private http = inject(HttpClient);
  private router = inject(Router);

  loginMessage = '';
  email = '';
  mot_de_passe = '';

  onLogin(): void {
    if (this.email && this.mot_de_passe) {
      this.handleLogin({
        email: this.email,
        mot_de_passe: this.mot_de_passe
      });
    } else {
      alert('Please enter both username and password');
    }
  }

  onEmailChange(event: any): void {
    this.email = event.target.value;
  }

  onMotDePasseChange(event: any): void {
    this.mot_de_passe = event.target.value;
  }

  handleLogin(credentials: { email: string; mot_de_passe: string }) {
    this.loginMessage = `Connexion en tant que ${credentials.email}...`;

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
        this.router.navigate(['/dashboardpage'], { replaceUrl: true });
        console.log('Navigation to dashboard successful');
      },
      error: () => {
        this.loginMessage = 'Login a échoué. Veuillez vérifier vos identifiants.';
      }
    });
  }
}
