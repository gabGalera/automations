#pragma once

#include <NativeModules.h>

namespace winrt::AutomacoesPainel::implementation {

REACT_MODULE(AgentLauncher);
struct AgentLauncher {
  REACT_METHOD(EnsureRunning);
  void EnsureRunning(
      std::string painelRoot,
      ::React::ReactPromise<void> &&result) noexcept;
};

} // namespace winrt::AutomacoesPainel::implementation
