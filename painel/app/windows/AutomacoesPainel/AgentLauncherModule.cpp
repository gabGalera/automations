#include "pch.h"
#include "AgentLauncherModule.h"

#include <string>
#include <vector>

namespace winrt::AutomacoesPainel::implementation {

void AgentLauncher::EnsureRunning(
    std::string painelRoot,
    ::React::ReactPromise<void> &&result) noexcept {
  STARTUPINFOW startupInfo{};
  startupInfo.cb = sizeof(startupInfo);
  startupInfo.dwFlags = STARTF_USESHOWWINDOW;
  startupInfo.wShowWindow = SW_HIDE;

  PROCESS_INFORMATION processInfo{};
  std::wstring workingDirectory = winrt::to_hstring(painelRoot);
  std::wstring commandLine = L"python.exe -m agent";
  std::vector<wchar_t> mutableCommand(commandLine.begin(), commandLine.end());
  mutableCommand.push_back(L'\0');

  const BOOL created = CreateProcessW(
      nullptr,
      mutableCommand.data(),
      nullptr,
      nullptr,
      FALSE,
      CREATE_NO_WINDOW | DETACHED_PROCESS,
      nullptr,
      workingDirectory.c_str(),
      &startupInfo,
      &processInfo);

  if (!created) {
    result.Reject("Falha ao iniciar o agente Python");
    return;
  }

  CloseHandle(processInfo.hProcess);
  CloseHandle(processInfo.hThread);
  result.Resolve();
}

} // namespace winrt::AutomacoesPainel::implementation
