import { Component, EventEmitter, Output, Input } from '@angular/core';
import { InputComponent } from '../InputComponent/InputComponent';
import { ButtonComponent } from '../ButtonComponent/ButtonComponent';
import { NgIf } from '@angular/common';


@Component({
  selector: 'LoginComponent',
  imports: [InputComponent, ButtonComponent, NgIf],
  templateUrl: './LoginComponent.html',
  styleUrls: ['./LoginComponent.css'],
  standalone: true
})
export class LoginComponent {
  email = '';
  mot_de_passe = '';
  
  @Input() loginMessage: string | null = null;

  @Output() loginAttempt = new EventEmitter<{ email: string; mot_de_passe: string }>();

  onLogin(): void {
    if (this.email && this.mot_de_passe) {
      this.loginAttempt.emit({
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
}
