import { Component, Input, Output, EventEmitter, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'InputComponent',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './InputComponent.html',
  styleUrl: './InputComponent.css'
})
export class InputComponent {
  @Input() id: string = '';
  @Input() name: string = '';
  @Input() type: string = 'text';
  @Input() placeholder: string = '';

  ngOnInit() {
    if (!this.placeholder) {
      switch (this.type) {
        case 'email':
          this.placeholder = 'Saisissez votre Email';
          break;
        case 'password':
          this.placeholder = 'Saisissez votre mot de passe';
          break;
        case 'number':
          this.placeholder = 'Saisissez un nombre';
          break;
        case 'tel':
          this.placeholder = 'Saisissez votre numéro de téléphone';
          break;
        case 'search':
          this.placeholder = 'Recherchez...';
          break;
        case 'url':
          this.placeholder = 'Saisissez une URL';
          break;
        default:
          this.placeholder = 'Saisissez une valeur';
      }
    }
  }
  @Input() label: string = '';
  @Input() value: string = '';
  @Input() required: boolean = false;
  @Input() variant: 'text' | 'number' | 'password' | 'email' | 'tel' | 'search' | 'url' = 'text';
  @Input() disabled: boolean = false;

  @Output() valueChange = new EventEmitter<string>();

  onInput(event: any) {
    this.value = event.target.value;
    this.valueChange.emit(this.value);
  }
}