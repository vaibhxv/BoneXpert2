import { useEffect, useState } from 'react';
import { getHealth, type BoneAgeHealth } from '../lib/api';

type State =
  | { kind: 'checking' }
  | { kind: 'up'; health: BoneAgeHealth }
  | { kind: 'down' };

/** Live readout of the inference engine status (polls the gateway). */
export function HealthBadge() {
  const [state, setState] = useState<State>({ kind: 'checking' });

  useEffect(() => {
    let alive = true;
    const controller = new AbortController();

    const check = async () => {
      try {
        const health = await getHealth(controller.signal);
        if (alive) setState({ kind: 'up', health });
      } catch {
        if (alive) setState({ kind: 'down' });
      }
    };

    check();
    const id = setInterval(check, 15000);
    return () => {
      alive = false;
      controller.abort();
      clearInterval(id);
    };
  }, []);

  const online = state.kind === 'up' && state.health.models_loaded;
  const label =
    state.kind === 'checking'
      ? 'Linking engine'
      : state.kind === 'down'
        ? 'Engine offline'
        : online
          ? `Engine ready · ${state.health.device.toUpperCase()}`
          : 'Warming models';

  return (
    <div className="health" data-online={online} data-down={state.kind === 'down'}>
      <span className="health__dot" />
      <span className="mono health__label">{label}</span>
    </div>
  );
}
