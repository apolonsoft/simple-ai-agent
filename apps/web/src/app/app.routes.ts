import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { guestGuard } from './core/guards/guest.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'chat',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/chat/chat-layout/chat-layout.component').then(
        (m) => m.ChatLayoutComponent
      ),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/chat/chat-window/chat-window.component').then(
            (m) => m.ChatWindowComponent
          ),
      },
      {
        path: ':sessionId',
        loadComponent: () =>
          import('./features/chat/chat-window/chat-window.component').then(
            (m) => m.ChatWindowComponent
          ),
      },
    ],
  },
  {
    path: '',
    redirectTo: 'chat',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: 'chat',
  },
];
