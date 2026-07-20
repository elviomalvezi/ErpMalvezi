import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthStore } from '../stores/auth.store';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authStore = inject(AuthStore);
  const router = inject(Router);
  const token = authStore.token();

  const request = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(request).pipe(
    catchError((err: HttpErrorResponse) => {
      // Token expirado/inválido: limpa a sessão e volta ao login.
      // Ignora o próprio endpoint de login para não mascarar "credenciais inválidas".
      if (err.status === 401 && !req.url.includes('/auth/login')) {
        authStore.clearAuth();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    }),
  );
};
