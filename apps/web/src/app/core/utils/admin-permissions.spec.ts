import { describe, it, expect } from 'vitest';
import { canBanUser, canChangeUserRole } from './admin-permissions';

describe('admin-permissions', () => {
  const regularUser = { id: 'u1', role: 'user' };
  const admin = { id: 'a1', role: 'admin' };
  const otherAdmin = { id: 'a2', role: 'admin' };
  const superAdmin = { id: 'sa1', role: 'super_admin' };
  const otherSuperAdmin = { id: 'sa2', role: 'super_admin' };

  describe('canBanUser', () => {
    it('returns false when actor or target is missing', () => {
      expect(canBanUser(null, regularUser)).toBe(false);
      expect(canBanUser(admin, null)).toBe(false);
      expect(canBanUser(undefined, undefined)).toBe(false);
    });

    it('prevents self-ban for any role', () => {
      expect(canBanUser(admin, admin)).toBe(false);
      expect(canBanUser(superAdmin, superAdmin)).toBe(false);
    });

    it('prevents banning super_admin by anyone', () => {
      expect(canBanUser(admin, superAdmin)).toBe(false);
      expect(canBanUser(superAdmin, otherSuperAdmin)).toBe(false);
    });

    it('allows admin to ban regular users but not other admins', () => {
      expect(canBanUser(admin, regularUser)).toBe(true);
      expect(canBanUser(admin, otherAdmin)).toBe(false);
    });

    it('allows super_admin to ban regular users and admins', () => {
      expect(canBanUser(superAdmin, regularUser)).toBe(true);
      expect(canBanUser(superAdmin, admin)).toBe(true);
    });
  });

  describe('canChangeUserRole', () => {
    it('returns false when actor or target is missing', () => {
      expect(canChangeUserRole(null, regularUser)).toBe(false);
      expect(canChangeUserRole(superAdmin, null)).toBe(false);
    });

    it('denies role changes for non-super_admin actors', () => {
      expect(canChangeUserRole(regularUser, regularUser)).toBe(false);
      expect(canChangeUserRole(admin, regularUser)).toBe(false);
      expect(canChangeUserRole(admin, otherAdmin)).toBe(false);
    });

    it('prevents super_admin from changing their own role', () => {
      expect(canChangeUserRole(superAdmin, superAdmin)).toBe(false);
    });

    it('allows super_admin to change roles of other users and admins', () => {
      expect(canChangeUserRole(superAdmin, regularUser)).toBe(true);
      expect(canChangeUserRole(superAdmin, admin)).toBe(true);
      expect(canChangeUserRole(superAdmin, otherSuperAdmin)).toBe(true);
    });
  });
});
