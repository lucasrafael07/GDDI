# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from datetime import date, timedelta
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from .db import AppConfig
from .controller import run_period
from .utils import parse_br_date
from .iqvia_api import test_comm

APP_TITLE = "GDDI – Gerador de dados IQVIA — by Aurora Business Intelligence"

class App(tb.Window):
    def __init__(self):
        self.cfg = AppConfig.load()
        super().__init__(title=APP_TITLE, themename=self.cfg.theme or "darkly")
        # style handler (avoid assigning to .style property)
        self._styler = tb.Style(theme=self.cfg.theme or "darkly")
        self._center(1200, 820)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._load_cfg()

    def _center(self, w:int, h:int):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Header
        top = tb.Frame(self, padding=8)
        top.pack(fill=X)
        tb.Label(top, text="GDDI", font=("Segoe UI", 18, "bold")).pack(side=TOP, anchor="center")
        tb.Label(top, text=APP_TITLE, font=("Segoe UI", 10)).pack(side=TOP, anchor="center")

        nb = tb.Notebook(self, bootstyle="dark")
        nb.pack(fill=BOTH, expand=YES, padx=8, pady=8)
        self.tab_run = tb.Frame(nb, padding=8)
        self.tab_cfg = tb.Frame(nb, padding=8)
        self.tab_about = tb.Frame(nb, padding=8)
        nb.add(self.tab_run, text="Execução")
        nb.add(self.tab_cfg, text="Configurações")
        nb.add(self.tab_about, text="Sobre")

        # Execução
        r1 = tb.Frame(self.tab_run)
        r1.pack(fill=X, pady=4)
        tb.Label(r1, text="Data Inicial:").pack(side=LEFT)
        self.dt_ini = DateEntry(r1, dateformat="%d/%m/%Y")
        self.dt_ini.pack(side=LEFT, padx=6)
        tb.Label(r1, text="Data Final:").pack(side=LEFT, padx=(12,0))
        self.dt_fim = DateEntry(r1, dateformat="%d/%m/%Y")
        self.dt_fim.pack(side=LEFT, padx=6)

        self.var_upload = tb.BooleanVar(value=self.cfg.upload_default)
        tb.Checkbutton(r1, text="Enviar para a IQVIA após zipar", variable=self.var_upload,
                       bootstyle="success-round-toggle").pack(side=LEFT, padx=12)

        r2 = tb.Frame(self.tab_run)
        r2.pack(fill=X, pady=6)
        tb.Label(r2, text="Pasta de saída:").pack(side=LEFT)
        self.out_var = tb.StringVar(value=self.cfg.out_dir)
        tb.Entry(r2, textvariable=self.out_var).pack(side=LEFT, fill=X, expand=YES, padx=6)
        tb.Button(r2, text="Selecionar…", command=self._pick_out, bootstyle="info-outline").pack(side=LEFT)

        r3 = tb.Frame(self.tab_run)
        r3.pack(fill=X, pady=6)
        tb.Button(r3, text="Gerar agora", command=self._on_generate, bootstyle="success").pack(side=LEFT)
        tb.Button(r3, text="Testar conexão Oracle", command=self._test_conn, bootstyle="secondary").pack(side=LEFT, padx=6)
        tb.Button(r3, text="Testar comunicação IQVIA", command=self._test_iqvia, bootstyle="info").pack(side=LEFT, padx=6)
        tb.Button(r3, text="Abrir saída", command=self._open_out, bootstyle="secondary-outline").pack(side=LEFT, padx=6)

        self.pbar = tb.Progressbar(self.tab_run, mode="determinate")
        self.pbar.pack(fill=X, pady=6)

        self.txt = ScrolledText(self.tab_run, height=26)
        self.txt.pack(fill=BOTH, expand=YES, pady=(6,4))

        # Configurações
        fc = tb.Frame(self.tab_cfg)
        fc.pack(fill=BOTH, expand=YES)

        lf_db = tb.Labelframe(fc, text="Oracle / Instant Client")
        lf_db.pack(fill=X, padx=4, pady=4)
        self.ic_var = self._row(lf_db, "Instant Client", self.cfg.instant_client_dir, picker=True)
        self.host_var = self._row(lf_db, "Host", self.cfg.db_host)
        self.port_var = self._row(lf_db, "Porta", str(self.cfg.db_port))
        self.sid_var = self._row(lf_db, "SID", self.cfg.db_sid)
        self.user_var = self._row(lf_db, "Usuário", self.cfg.db_user)
        self.pass_var = self._row(lf_db, "Senha", self.cfg.db_pass, show="*")

        lf_iq = tb.Labelframe(fc, text="IQVIA")
        lf_iq.pack(fill=X, padx=4, pady=4)
        self.cid_var = self._row(lf_iq, "Client ID", self.cfg.iqvia_client_id)
        self.csec_var = self._row(lf_iq, "Client Secret", self.cfg.iqvia_client_secret, show="*")
        self.tokurl_var = self._row(lf_iq, "Token URL", self.cfg.iqvia_token_url)
        self.upurl_var = self._row(lf_iq, "Upload URL", self.cfg.iqvia_upload_url)
        self.codiq_var = self._row(lf_iq, "Cod IQVIA (estab.)", self.cfg.codiqvia)
        self.filial_var = self._row(lf_iq, "Filial (fixa)", str(self.cfg.codfilial))

        lf_pref = tb.Labelframe(fc, text="Preferências / Validação / Tema")
        lf_pref.pack(fill=X, padx=4, pady=4)
        self.out_cfg_var = self._row(lf_pref, "Pasta de saída", self.cfg.out_dir, picker=True)
        self.val_enabled = tb.BooleanVar(value=self.cfg.validation_enabled)
        tb.Checkbutton(lf_pref, text="Validar JSON (leve) antes de salvar", variable=self.val_enabled,
                       bootstyle="warning-round-toggle").pack(anchor="w", padx=6, pady=4)
        self.layout_path_var = self._row(lf_pref, "Layout JSON oficial (opcional)", self.cfg.layout_example_path, picker=True)
        tb.Label(lf_pref, text="Tema:").pack(side=LEFT, padx=(6,2))
        self.theme_var = tb.StringVar(value=self.cfg.theme or "darkly")
        self.theme_combo = tb.Combobox(lf_pref, textvariable=self.theme_var, values=sorted(tb.Style().theme_names()), width=22)
        self.theme_combo.pack(side=LEFT, padx=6)
        tb.Button(lf_pref, text="Aplicar tema", command=self._apply_theme, bootstyle="warning-outline").pack(side=LEFT, padx=8)

        tb.Button(fc, text="Salvar configurações", command=self._save_cfg, bootstyle="primary").pack(side=RIGHT, pady=8)

        # Sobre
        sa = self.tab_about
        tb.Label(sa, text="GDDI – Gerador de dados IQVIA", font=("Segoe UI", 14, "bold")).pack(pady=(4,2))
        tb.Label(sa, text="by Aurora Business Intelligence", font=("Segoe UI", 10)).pack()
        tb.Label(sa, text="Função: extrair dados do WinThor (Oracle), montar JSON diário no layout IQVIA, zipar e enviar (opcional).", wraplength=900, justify=LEFT).pack(pady=6)
        def _open_doc():
            import webbrowser; webbrowser.open("https://dataentry.solutions.iqvia.com/doc/")
        tb.Button(sa, text="Abrir documentação oficial da IQVIA", command=_open_doc, bootstyle="info-outline").pack(pady=4)

    # helpers
    def _row(self, parent, label, value, show=None, picker=False):
        r = tb.Frame(parent)
        r.pack(fill=X, pady=2)
        tb.Label(r, text=label+":").pack(side=LEFT, padx=(6,6))
        var = tb.StringVar(value=value)
        ent = tb.Entry(r, textvariable=var, show=show)
        ent.pack(side=LEFT, fill=X, expand=YES, padx=(0,6))
        if picker:
            tb.Button(r, text="...", width=3, command=lambda v=var: self._pick_path(v), bootstyle="info-outline").pack(side=LEFT)
        return var

    def _pick_path(self, var):
        p = filedialog.askdirectory(title="Escolha a pasta")
        if p:
            var.set(p)

    def _pick_out(self):
        p = filedialog.askdirectory(title="Escolha a pasta de saída")
        if p:
            self.out_var.set(p)

    def _open_out(self):
        p = Path(self.out_var.get().strip())
        if not p.exists():
            self._log("📁 Pasta de saída ainda não existe.")
            return
        os.startfile(str(p))

    def _apply_theme(self):
        t = self.theme_var.get().strip() or "darkly"
        try:
            self._styler.theme_use(t)
            self.cfg.theme = t
            self.cfg.save()
            self._log(f"🎨 Tema '{t}' aplicado.")
        except Exception as e:
            messagebox.showerror("Erro tema", str(e))

    def _load_cfg(self):
        # datas default: ontem/anteontem
        if not self.cfg.last_ini:
            d0 = date.today() - timedelta(days=2)
            self.cfg.last_ini = d0.strftime("%d/%m/%Y")
        if not self.cfg.last_fim:
            d1 = date.today() - timedelta(days=1)
            self.cfg.last_fim = d1.strftime("%d/%m/%Y")
        self.dt_ini.entry.delete(0, END); self.dt_ini.entry.insert(0, self.cfg.last_ini)
        self.dt_fim.entry.delete(0, END); self.dt_fim.entry.insert(0, self.cfg.last_fim)

    def _save_cfg(self):
        try:
            self.cfg.instant_client_dir = self.ic_var.get().strip()
            self.cfg.db_host = self.host_var.get().strip()
            self.cfg.db_port = int(self.port_var.get().strip() or "1521")
            self.cfg.db_sid = self.sid_var.get().strip()
            self.cfg.db_user = self.user_var.get().strip()
            self.cfg.db_pass = self.pass_var.get().strip()

            self.cfg.iqvia_client_id = self.cid_var.get().strip()
            self.cfg.iqvia_client_secret = self.csec_var.get().strip()
            self.cfg.iqvia_token_url = self.tokurl_var.get().strip()
            self.cfg.iqvia_upload_url = self.upurl_var.get().strip()
            self.cfg.codiqvia = self.codiq_var.get().strip()
            self.cfg.codfilial = int(self.filial_var.get().strip() or "1")

            self.cfg.out_dir = self.out_cfg_var.get().strip()
            self.cfg.upload_default = bool(self.var_upload.get())
            self.cfg.validation_enabled = bool(self.val_enabled.get())
            self.cfg.layout_example_path = self.layout_path_var.get().strip()
            self.cfg.theme = self.theme_var.get().strip() or self.cfg.theme

            self.cfg.last_ini = self.dt_ini.entry.get().strip()
            self.cfg.last_fim = self.dt_fim.entry.get().strip()
            self.cfg.save()
            self._log("💾 Configurações salvas.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _log(self, msg: str):
        self.txt.insert(END, msg + "\n")
        self.txt.see(END)
        self.update_idletasks()

    def _test_conn(self):
        self._save_cfg()
        self._log("🔌 Testando conexão Oracle...")
        from .db import test_connection
        try:
            res = test_connection(self.cfg)
            self._log("✅ " + res)
        except Exception as e:
            self._log("❌ Falha: " + str(e))

    def _test_iqvia(self):
        self._save_cfg()
        self._log("🌐 Testando autenticação IQVIA...")
        ok = test_comm(self.cfg.iqvia_token_url, self.cfg.iqvia_client_id, self.cfg.iqvia_client_secret, logger=self._log)
        self._log("✅ OK" if ok else "❌ Falha")

    def _on_generate(self):
        self._save_cfg()
        self.txt.delete("1.0", END)
        self._log("Integração Winthor x Iqvia.")
        self._log("Aguardando Execução...")
        try:
            d0 = parse_br_date(self.dt_ini.entry.get().strip())
            d1 = parse_br_date(self.dt_fim.entry.get().strip())
        except Exception:
            messagebox.showerror("Erro", "Datas inválidas. Use o calendário (dd/mm/aaaa).")
            return

        def logger(m): self._log(m)
        try:
            run_period(self.cfg, d0, d1, upload=bool(self.var_upload.get()), logger=logger,
                       validate=bool(self.val_enabled.get()), example_layout=self.layout_path_var.get().strip())
        except Exception as e:
            self._log("❌ ERRO: " + str(e))

    def _on_close(self):
        try:
            self._save_cfg()
        finally:
            self.destroy()

def run_app():
    App().mainloop()
