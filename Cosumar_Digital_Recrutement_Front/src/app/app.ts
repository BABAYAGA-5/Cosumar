import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('Cosumar_Digital_Recrutement_Front');
  protected readonly isLoggedIn = signal(false);

  responseData: any;
  onSubmit() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    fetch(environment.apiUrl + 'auth/test', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      signal: controller.signal
    })
    .then(response => {
      clearTimeout(timeout);
      if (!response.ok) {
        if (response.status === 0) {
          throw new Error('Server is down');
        }
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      this.responseData = data;
      if (data) {
        this.isLoggedIn.set(true);
      } else {
        this.isLoggedIn.set(false);
      }
    })
    .catch(error => {
      clearTimeout(timeout);
      if (error.name === 'AbortError') {
        this.responseData = { message: 'Request timed out' };
      } else if (error.message === 'Server is down') {
        this.responseData = { message: 'Server is down or unreachable' };
      } else {
        console.error('Error:', error);
        this.responseData = { message: 'Error occurred' };
      }
    });
  }
}