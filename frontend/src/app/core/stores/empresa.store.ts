import { computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap } from 'rxjs';

import { EmpresaService } from '../services/empresa.service';
import { EmpresaListItem } from '../models';

export type Empresa = {
  id: string;
  nome: string;
  tipo: 'PJ' | 'PF';
  documento: string | null;
};

interface EmpresaState {
  empresas: Empresa[];
  empresaAtiva: Empresa | null;
  modoSimultaneo: boolean;
  carregando: boolean;
}

function toEmpresa(e: EmpresaListItem): Empresa {
  return {
    id: e.id,
    nome: e.nome_alternativo ?? e.nome_principal,
    tipo: e.tipo,
    documento: e.documento,
  };
}

export const EmpresaStore = signalStore(
  { providedIn: 'root' },
  withState<EmpresaState>({
    empresas: [],
    empresaAtiva: null,
    modoSimultaneo: false,
    carregando: false,
  }),
  withComputed((state) => ({
    empresasVisiveis: computed(() =>
      state.modoSimultaneo()
        ? state.empresas()
        : state.empresaAtiva()
          ? [state.empresaAtiva()!]
          : [],
    ),
  })),
  withMethods((store, empresaService = inject(EmpresaService), router = inject(Router)) => ({
    carregar: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { carregando: true })),
        switchMap(() => empresaService.listar()),
        tap((lista) => {
          const empresas = lista.map(toEmpresa);
          const empresaAtiva = empresas.length > 0 ? empresas[0] : null;
          patchState(store, { empresas, empresaAtiva, carregando: false });
        }),
      ),
    ),
    selecionarEmpresa(empresa: Empresa): void {
      patchState(store, { empresaAtiva: empresa });
      router.navigate(['/dashboard']);
    },
    toggleModoSimultaneo(): void {
      patchState(store, { modoSimultaneo: !store.modoSimultaneo() });
    },
    popular(lista: Empresa[]): void {
      patchState(store, { empresas: lista });
    },
    limpar(): void {
      patchState(store, { empresas: [], empresaAtiva: null });
    },
  })),
);
