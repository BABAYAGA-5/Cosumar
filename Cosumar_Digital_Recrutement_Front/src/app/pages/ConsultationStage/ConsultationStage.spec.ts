import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConsultationStage } from './ConsultationStage';

describe('ConsultationStage', () => {
  let component: ConsultationStage;
  let fixture: ComponentFixture<ConsultationStage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConsultationStage]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ConsultationStage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
