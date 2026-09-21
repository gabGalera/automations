import React from 'react';
import {StyleSheet, Switch, Text, View} from 'react-native';
import type {Automacao} from '../api';

type Props = {
  automacao: Automacao;
  busy: boolean;
  onToggle: (id: string, ligar: boolean) => void;
};

export function AutomacaoCard({automacao, busy, onToggle}: Props) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.titulo}>{automacao.titulo}</Text>
        <Switch
          value={automacao.ligado}
          disabled={busy}
          onValueChange={value => onToggle(automacao.id, value)}
        />
      </View>
      <Text style={styles.status}>
        {automacao.ligado ? 'Watcher ligado' : 'Watcher desligado'}
      </Text>
      <Text style={styles.pasta}>{automacao.pasta}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  titulo: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  status: {
    marginTop: 8,
    fontSize: 14,
    color: '#374151',
  },
  pasta: {
    marginTop: 8,
    fontSize: 12,
    color: '#6b7280',
  },
});
