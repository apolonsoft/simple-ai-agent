export interface PermissionActor {
  id: string;
  role: string;
}

/**
 * Returns whether `actor` is allowed to moderate (ban or unban) `target` based on role hierarchy.
 */
export function canModerateUser(
  actor: PermissionActor | null | undefined,
  target: PermissionActor | null | undefined
): boolean {
  if (!actor || !target) return false;
  if (target.id === actor.id) return false;
  if (target.role === 'super_admin') return false;
  if (target.role === 'admin' && actor.role !== 'super_admin') return false;
  return true;
}

/**
 * Alias for `canModerateUser` preserved for backwards compatibility.
 */
export const canBanUser = canModerateUser;

/**
 * Returns whether `actor` is allowed to change `target`'s role.
 */
export function canChangeUserRole(
  actor: PermissionActor | null | undefined,
  target: PermissionActor | null | undefined
): boolean {
  if (!actor || !target) return false;
  if (actor.role !== 'super_admin') return false;
  if (target.id === actor.id) return false;
  return true;
}
