import { computed, inject } from '@angular/core';
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';

interface AuthState {
  token: string | null;
  userId: string | null;
  nome: string | null;
  admin: boolean;
  gestor: boolean;
}

const initialState: AuthState = {
  token: localStorage.getItem('auth_token'),
  userId: localStorage.getItem('auth_user_id'),
  nome: localStorage.getItem('auth_nome'),
  admin: localStorage.getItem('auth_admin') === 'true',
  gestor: localStorage.getItem('auth_gestor') === 'true',
};

export const AuthStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed((state) => ({
    isAuthenticated: computed(() => !!state.token()),
  })),
  withMethods((store) => ({
    setToken(token: string): void {
      localStorage.setItem('auth_token', token);
      patchState(store, { token });
    },
    setUsuario(userId: string, nome: string, admin: boolean, gestor = false): void {
      localStorage.setItem('auth_user_id', userId);
      localStorage.setItem('auth_nome', nome);
      localStorage.setItem('auth_admin', String(admin));
      localStorage.setItem('auth_gestor', String(gestor));
      patchState(store, { userId, nome, admin, gestor });
    },
    setAuth(token: string, userId: string, nome: string, admin = false, gestor = false): void {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user_id', userId);
      localStorage.setItem('auth_nome', nome);
      localStorage.setItem('auth_admin', String(admin));
      localStorage.setItem('auth_gestor', String(gestor));
      patchState(store, { token, userId, nome, admin, gestor });
    },
    clearAuth(): void {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user_id');
      localStorage.removeItem('auth_nome');
      localStorage.removeItem('auth_admin');
      localStorage.removeItem('auth_gestor');
      patchState(store, { token: null, userId: null, nome: null, admin: false, gestor: false });
    },
  }))
);
