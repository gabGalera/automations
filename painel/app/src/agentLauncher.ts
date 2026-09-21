import {NativeModules, Platform} from 'react-native';
import {PAINEL_ROOT} from './config';

type AgentLauncherModule = {
  ensureRunning: (painelRoot: string) => Promise<void>;
};

const NativeAgentLauncher: AgentLauncherModule | undefined =
  NativeModules.AgentLauncher;

export async function ensureAgentRunning(): Promise<void> {
  if (Platform.OS !== 'windows') {
    return;
  }
  if (!NativeAgentLauncher?.ensureRunning) {
    throw new Error(
      'Modulo nativo AgentLauncher indisponivel. Recompile o app Windows.',
    );
  }
  await NativeAgentLauncher.ensureRunning(PAINEL_ROOT);
}
