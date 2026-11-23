import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BanUserModalComponent } from './ban-user-modal.component';
import { AdminUser } from '../../../core/models/admin.model';

describe('BanUserModalComponent', () => {
  let component: BanUserModalComponent;
  let fixture: ComponentFixture<BanUserModalComponent>;

  const targetUser: AdminUser = {
    id: 'u-1',
    email: 'bob@example.com',
    full_name: 'Bob Builder',
    role: 'user',
    is_active: true,
    is_banned: false,
    banned_at: null,
    ban_reason: null,
    created_at: '2026-01-01T00:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BanUserModalComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(BanUserModalComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('targetUser', targetUser);
    fixture.detectChanges();
  });

  it('should render target user info with dialog ARIA attributes', () => {
    const dialog = (fixture.nativeElement as HTMLElement).querySelector('[role="dialog"]');
    expect(dialog).toBeTruthy();
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(dialog?.textContent).toContain('Bob Builder');
    expect(dialog?.textContent).toContain('bob@example.com');
  });

  it('should emit trimmed reason on confirm', () => {
    const confirmSpy = vi.fn();
    component.confirm.subscribe(confirmSpy);

    component.banReason.set('  Spamming links  ');
    component.onConfirm();

    expect(confirmSpy).toHaveBeenCalledWith('Spamming links');
  });

  it('should emit cancel on Escape when not submitting and ignore Escape while submitting', () => {
    const cancelSpy = vi.fn();
    component.cancel.subscribe(cancelSpy);

    fixture.componentRef.setInput('isSubmitting', true);
    fixture.detectChanges();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(cancelSpy).not.toHaveBeenCalled();

    fixture.componentRef.setInput('isSubmitting', false);
    fixture.detectChanges();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(cancelSpy).toHaveBeenCalledTimes(1);
  });
});
