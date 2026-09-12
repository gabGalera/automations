from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from consolidacao_base_2.processos import desligar_watcher, ligar_watcher, watcher_ligado
from consolidacao_base_2.watcher import HOSTNAME_PERMITIDO, PASTA_PADRAO, hostname_ok


def abrir_painel() -> None:
    raiz = tk.Tk()
    raiz.title("Consolidação confirmação MP")
    raiz.resizable(False, False)
    raiz.attributes("-topmost", True)

    ligado = tk.BooleanVar(value=watcher_ligado())
    status = tk.StringVar()

    def atualizar_rotulo() -> None:
        if ligado.get():
            status.set("Watcher ligado")
        else:
            status.set("Watcher desligado")

    def aplicar_toggle() -> None:
        if not hostname_ok():
            ligado.set(False)
            status.set(f"Hostname inválido (precisa ser {HOSTNAME_PERMITIDO})")
            return
        if not PASTA_PADRAO.is_dir():
            ligado.set(False)
            status.set(f"Pasta não encontrada:\n{PASTA_PADRAO}")
            return
        try:
            if ligado.get():
                ligar_watcher()
            else:
                desligar_watcher()
        except OSError as extra:
            ligado.set(watcher_ligado())
            status.set(f"Falha: {extra}")
            return
        raiz.after(400, sincronizar)

    def sincronizar() -> None:
        ligado.set(watcher_ligado())
        atualizar_rotulo()

    atualizar_rotulo()

    quadro = ttk.Frame(raiz, padding=16)
    quadro.grid(row=0, column=0)
    ttk.Label(quadro, textvariable=status, justify="center").grid(row=0, column=0, pady=(0, 12))
    ttk.Checkbutton(
        quadro,
        text="Ligar / desligar",
        variable=ligado,
        command=aplicar_toggle,
    ).grid(row=1, column=0)
    ttk.Label(
        quadro,
        text=str(PASTA_PADRAO),
        wraplength=360,
        foreground="#555",
    ).grid(row=2, column=0, pady=(12, 0))

    raiz.after(400, sincronizar)
    raiz.mainloop()
