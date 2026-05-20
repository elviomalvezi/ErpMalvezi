import { computed, inject } from '@angular/core';
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';

interface AuthState {
  token: string | null;
  userId: string | null;
  nome: string | null;
}

const initialState: AuthState = {
  token: localStorage.getItem('auth_token'),
  userId: localStorage.getItem('auth_user_id'),
  nome: localStorage.getItem('auth_nome'),
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
    setUsuario(userId: string, nome: string): void {
      localStorage.setItem('auth_user_id', userId);
      localStorage.setItem('auth_nome', nome);
      patchState(store, { userId, nome });
    },
    setAuth(token: string, userId: string, nome: string): void {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user_id', userId);
      localStorage.setItem('auth_nome', nome);
      patchState(store, { token, userId, nome });
    },
    clearAuth(): void {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user_id');
      localStorage.removeItem('auth_nome');
      patchState(store, { token: null, userId: null, nome: null });
    },
  }))
);
