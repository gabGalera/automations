import React, {useCallback, useEffect, useState} from 'react';
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  healthCheck,
  iniciarAutomacao,
  iniciarTodas,
  listarAutomacoes,
  pararAutomacao,
  pararTodas,
  type Automacao,
} from './src/api';
import {ensureAgentRunning} from './src/agentLauncher';
import {AutomacaoCard} from './src/components/AutomacaoCard';

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

  const conectarAgente = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      let online = await healthCheck();
      if (!online) {
        await ensureAgentRunning();
        for (let tentativa = 0; tentativa < 10; tentativa += 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
          online = await healthCheck();
          if (online) {
            break;
          }
        }
      }
      if (!online) {
        throw new Error('Agente nao respondeu em http://127.0.0.1:8765');
      }
      await sincronizar();
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : 'Falha ao conectar');
    } finally {
      setCarregando(false);
    }
  }, [sincronizar]);

  useEffect(() => {
    conectarAgente();
  }, [conectarAgente]);

  useEffect(() => {
    if (carregando || erro) {
      return;
    }
    const timer = setInterval(() => {
      sincronizar().catch(() => undefined);
    }, POLL_MS);
    return () => clearInterval(timer);
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
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.container}>
        <Text style={styles.tituloApp}>Painel de Automações</Text>

        {carregando ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#2563eb" />
            <Text style={styles.subtitulo}>Conectando ao agente...</Text>
          </View>
        ) : erro ? (
          <View style={styles.center}>
            <Text style={styles.erro}>{erro}</Text>
            <Pressable style={styles.botao} onPress={conectarAgente}>
              <Text style={styles.botaoTexto}>Tentar novamente</Text>
            </Pressable>
          </View>
        ) : (
          <>
            <View style={styles.acoes}>
              <Pressable
                style={[styles.botao, styles.botaoSecundario, busy && styles.disabled]}
                disabled={busy}
                onPress={ligarTodos}>
                <Text style={styles.botaoTexto}>Ligar todos</Text>
              </Pressable>
              <Pressable
                style={[styles.botao, styles.botaoPerigo, busy && styles.disabled]}
                disabled={busy}
                onPress={desligarTodos}>
                <Text style={styles.botaoTexto}>Desligar todos</Text>
              </Pressable>
            </View>
            <ScrollView contentContainerStyle={styles.lista}>
              {automacoes.map(item => (
                <AutomacaoCard
                  key={item.id}
                  automacao={item}
                  busy={busy}
                  onToggle={alternar}
                />
              ))}
            </ScrollView>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  container: {
    flex: 1,
    padding: 20,
  },
  tituloApp: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  subtitulo: {
    color: '#4b5563',
  },
  erro: {
    color: '#b91c1c',
    textAlign: 'center',
    marginBottom: 8,
  },
  acoes: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  botao: {
    flex: 1,
    backgroundColor: '#2563eb',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  botaoSecundario: {
    backgroundColor: '#059669',
  },
  botaoPerigo: {
    backgroundColor: '#dc2626',
  },
  botaoTexto: {
    color: '#fff',
    fontWeight: '600',
  },
  disabled: {
    opacity: 0.6,
  },
  lista: {
    paddingBottom: 24,
  },
});
