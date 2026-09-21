import type {Automacao} from '../api';

type Props = {
  automacao: Automacao;
  busy: boolean;
  onToggle: (id: string, ligar: boolean) => void;
};

export function AutomacaoCard({automacao, busy, onToggle}: Props) {
  return (
    <article className="card">
      <div className="card-header">
        <h2 className="card-titulo">{automacao.titulo}</h2>
        <label className="toggle">
          <input
            type="checkbox"
            checked={automacao.ligado}
            disabled={busy}
            onChange={event => onToggle(automacao.id, event.target.checked)}
          />
          <span className="toggle-track" />
        </label>
      </div>
      <p className="card-status">
        {automacao.ligado ? 'Watcher ligado' : 'Watcher desligado'}
      </p>
      <p className="card-pasta">{automacao.pasta}</p>
    </article>
  );
}
