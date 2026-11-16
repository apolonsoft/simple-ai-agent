import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

export const adminGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.getToken()) {
    return router.createUrlTree(['/login']);
  }

  const currentUser = authService.currentUser();
  if (currentUser) {
    if (currentUser.role === 'admin' || currentUser.role === 'super_admin') {
      return true;
    }
    return router.createUrlTree(['/chat']);
  }

  return authService.getMe().pipe(
    map((user) => {
      authService.currentUser.set(user);
      if (user.role === 'admin' || user.role === 'super_admin') {
        return true;
      }
      return router.createUrlTree(['/chat']);
    }),
    catchError(() => {
      authService.logout();
      return of(router.createUrlTree(['/login']));
    })
  );
};
