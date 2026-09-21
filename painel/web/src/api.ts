export type Automacao = {
  id: string;
  titulo: string;
  modulo: string;
  pasta: string;
  ligado: boolean;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {'Content-Type': 'application/json'},
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const data = await request<{status: string}>('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}

export function listarAutomacoes(): Promise<Automacao[]> {
  return request<Automacao[]>('/automacoes');
}

export function iniciarAutomacao(id: string): Promise<Automacao> {
  return request<Automacao>(`/automacoes/${id}/start`, {method: 'POST'});
}

export function pararAutomacao(id: string): Promise<Automacao> {
  return request<Automacao>(`/automacoes/${id}/stop`, {method: 'POST'});
}

export function iniciarTodas(): Promise<{resultados: Automacao[]}> {
  return request<{resultados: Automacao[]}>('/automacoes/start-all', {
    method: 'POST',
  });
}

export function pararTodas(): Promise<{resultados: Automacao[]}> {
  return request<{resultados: Automacao[]}>('/automacoes/stop-all', {
    method: 'POST',
  });
}
