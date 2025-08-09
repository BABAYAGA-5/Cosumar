import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'ButtonComponent',
  imports: [],
  templateUrl: './ButtonComponent.html',
  styleUrl: './ButtonComponent.css',
  standalone: true
})
export class ButtonComponent {
  @Input() variant: 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'outline' = 'primary';
  @Input() disabled: boolean = false;
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Output() buttonClick = new EventEmitter<void>();

  get buttonClass(): string {
    return `btn btn-${this.variant} btn-${this.size}`;
  }

  onClick(): void {
    this.buttonClick.emit();
  }

  handlePrimaryClick(): void {
    console.log('Primary button clicked');
  }

  handleSecondaryClick(): void {
    console.log('Secondary button clicked');
  }

  handleDangerClick(): void {
    console.log('Danger button clicked');
  }

  handleSuccessClick(): void {
    console.log('Success button clicked');
  }

  handleWarningClick(): void {
    console.log('Warning button clicked');
  }

  handleOutlineClick(): void {
    console.log('Outline button clicked');
  }
}
