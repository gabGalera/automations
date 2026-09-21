import {useCallback, useEffect, useState} from 'react';
import {
  healthCheck,
  iniciarAutomacao,
  iniciarTodas,
  listarAutomacoes,
  pararAutomacao,
  pararTodas,
  type Automacao,
} from './api';
import {AutomacaoCard} from './components/AutomacaoCard';

const POLL_MS = 4000;

export default function App() {
  const [automacoes, setAutomacoes] = useState<Automacao[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const sincronizar = useCallback(async () => {
    const lista = await listarAutomacoes();
    setAutomacoes(lista);
    setErro(null);
  }, []);

  const conectar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const online = await healthCheck();
      if (!online) {
        throw new Error(
          'Agente offline. Rode: python -m agent (na pasta painel/)',
        );
      }
      await sincronizar();
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : 'Falha ao conectar');
    } finally {
      setCarregando(false);
    }
  }, [sincronizar]);

  useEffect(() => {
    conectar();
  }, [conectar]);

  useEffect(() => {
    if (carregando || erro) {
      return;
    }
    const timer = window.setInterval(() => {
      sincronizar().catch(() => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [carregando, erro, sincronizar]);

  const alternar = async (id: string, ligar: boolean) => {
    setBusy(true);
    setErro(null);
    try {
      const atualizada = ligar
        ? await iniciarAutomacao(id)
        : await pararAutomacao(id);
      setAutomacoes(prev =>
        prev.map(item => (item.id === id ? atualizada : item)),
      );
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : 'Falha ao alternar');
      await sincronizar();
    } finally {
      setBusy(false);
    }
  };

  const ligarTodos = async () => {
    setBusy(true);
    setErro(null);
    try {
      const {resultados} = await iniciarTodas();
      setAutomacoes(resultados);
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : 'Falha ao ligar todos');
    } finally {
      setBusy(false);
    }
  };

  const desligarTodos = async () => {
    setBusy(true);
    setErro(null);
    try {
      const {resultados} = await pararTodas();
      setAutomacoes(resultados);
    } catch (falha) {
      setErro(
        falha instanceof Error ? falha.message : 'Falha ao desligar todos',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="layout">
      <header className="header">
        <h1>Painel de Automações</h1>
      </header>

      <main className="main">
        {carregando ? (
          <div className="center">
            <div className="spinner" />
            <p>Conectando ao agente...</p>
          </div>
        ) : erro ? (
          <div className="center">
            <p className="erro">{erro}</p>
            <button type="button" className="btn btn-primary" onClick={conectar}>
              Tentar novamente
            </button>
          </div>
        ) : (
          <>
            <div className="acoes">
              <button
                type="button"
                className="btn btn-success"
                disabled={busy}
                onClick={ligarTodos}>
                Ligar todos
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={busy}
                onClick={desligarTodos}>
                Desligar todos
              </button>
            </div>
            <div className="lista">
              {automacoes.map(item => (
                <AutomacaoCard
                  key={item.id}
                  automacao={item}
                  busy={busy}
                  onToggle={alternar}
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
