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
import json

from .db import AppConfig, connect_oracle, test_connection
from .controller import run_period, build_payload, save_json, get_layout_version, get_layout_changes
from .utils import parse_br_date, beautify_json
from .iqvia_api import test_comm, check_upload_status, get_token
from .sql_prisma import SQL_MOV, SQL_DEVOLUCOES, SQL_FILIAL, SQL_CLIENTES, SQL_ESTOQUE, SQL_PRODUTOS_UNICOS, SQL_ENTRADA_PRODUTOS

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
        # Versão do layout
        version_text = f"Layout v{get_layout_version()}"
        version_label = tb.Label(top, text=version_text, font=("Segoe UI", 8))
        version_label.pack(side=TOP, anchor="center")
        version_label.bind("<Button-1>", self._show_version_history)

        nb = tb.Notebook(self, bootstyle="dark")
        nb.pack(fill=BOTH, expand=YES, padx=8, pady=8)
        self.tab_run = tb.Frame(nb, padding=8)
        self.tab_cfg = tb.Frame(nb, padding=8)
        self.tab_monitor = tb.Frame(nb, padding=8) # Nova aba para monitoramento
        self.tab_about = tb.Frame(nb, padding=8)
        nb.add(self.tab_run, text="Execução")
        nb.add(self.tab_cfg, text="Configurações")
        nb.add(self.tab_monitor, text="Monitor de Uploads")
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
        # Novo botão para visualização prévia do JSON
        tb.Button(r3, text="Visualizar JSON", command=self._preview_json, bootstyle="warning").pack(side=LEFT, padx=6)

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

        # Monitor de Uploads
        tm = self.tab_monitor
        tb.Label(tm, text="Monitor de Status de Uploads", font=("Segoe UI", 14, "bold")).pack(pady=(4,10))

        tm1 = tb.Frame(tm)
        tm1.pack(fill=X, pady=4)
        tb.Label(tm1, text="GUID do Upload:").pack(side=LEFT, padx=(6,6))
        self.guid_var = tb.StringVar()
        tb.Entry(tm1, textvariable=self.guid_var, width=40).pack(side=LEFT, padx=(0,10))
        tb.Button(tm1, text="Verificar Status", command=self._check_upload_status, bootstyle="info").pack(side=LEFT)
        tb.Button(tm1, text="Limpar", command=lambda: self.monitor_txt.delete(1.0, END), bootstyle="secondary-outline").pack(side=LEFT, padx=6)

        tm2 = tb.Frame(tm)
        tm2.pack(fill=X, pady=4)
        tb.Label(tm2, text="Histórico de uploads recentes:").pack(side=LEFT, padx=(6,6))
        tb.Button(tm2, text="Carregar", command=self._load_recent_uploads, bootstyle="secondary").pack(side=LEFT, padx=6)

        self.monitor_txt = ScrolledText(tm, height=26)
        self.monitor_txt.pack(fill=BOTH, expand=YES, pady=(6,4))

        # Sobre
        sa = self.tab_about
        tb.Label(sa, text="GDDI – Gerador de dados IQVIA", font=("Segoe UI", 14, "bold")).pack(pady=(4,2))
        tb.Label(sa, text="by Aurora Business Intelligence", font=("Segoe UI", 10)).pack()
        tb.Label(sa, text="Função: extrair dados do WinThor (Oracle), montar JSON diário no layout IQVIA, zipar e enviar (opcional).", wraplength=900, justify=LEFT).pack(pady=6)
        def _open_doc():
            import webbrowser; webbrowser.open("https://dataentry.solutions.iqvia.com/doc/")
        tb.Button(sa, text="Abrir documentação oficial da IQVIA", command=_open_doc, bootstyle="info-outline").pack(pady=4)
        
        # Exibir versão e histórico
        version_frame = tb.Frame(sa)
        version_frame.pack(pady=10)
        tb.Label(version_frame, text=f"Versão do Layout: {get_layout_version()}", font=("Segoe UI", 10, "bold")).pack(pady=2)
        tb.Button(version_frame, text="Ver histórico de alterações", command=self._show_version_history, bootstyle="secondary-outline").pack(pady=2)

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

    # --- Novas funções implementadas ---
    
    def _preview_json(self):
        """Mostra visualização prévia do JSON para um dia selecionado"""
        try:
            d0 = parse_br_date(self.dt_ini.entry.get().strip())
            
            self._log("🔍 Gerando prévia do JSON para o dia " + d0.strftime("%d/%m/%Y") + "...")
            
            # Conecta ao Oracle e gera o payload para um único dia
            conn = connect_oracle(self.cfg)
            try:
                # Consultas para um único dia
                from .db import fetch_df
                
                # Carregar dados
                mov = fetch_df(conn, SQL_MOV, DIA=d0, CODFILIAL=self.cfg.codfilial)
                dev = fetch_df(conn, SQL_DEVOLUCOES, DIA=d0, CODFILIAL=self.cfg.codfilial)
                fil = fetch_df(conn, SQL_FILIAL, DIA=d0, CODFILIAL=self.cfg.codfilial)
                cli = fetch_df(conn, SQL_CLIENTES, DIA=d0, CODFILIAL=self.cfg.codfilial)
                est = fetch_df(conn, SQL_ESTOQUE, DIA=d0, CODFILIAL=self.cfg.codfilial)
                produtos_unicos = fetch_df(conn, SQL_PRODUTOS_UNICOS, DIA=d0, CODFILIAL=self.cfg.codfilial)
                entradas = fetch_df(conn, SQL_ENTRADA_PRODUTOS, DIA=d0, CODFILIAL=self.cfg.codfilial)
                
                # Preparar dados de entrada
                dados_entrada = {}
                for r in entradas.itertuples(index=False):
                    dados_entrada[int(getattr(r, "CODPROD"))] = {
                        "ean": getattr(r, "CODAUXILIAR", "") or "",
                        "preco": float(getattr(r, "PTABELA", 0.0) or 0.0)
                    }
                
                # Gerar payload
                payload = build_payload(
                    mov, dev, fil, cli, est, produtos_unicos, dados_entrada,
                    d0, self.cfg.iqvia_client_id, self.cfg.codiqvia, self._log
                )
                
                self._log(f"✅ Prévia gerada com sucesso! Exibindo em nova janela...")
                
                # Exibir prévia em nova janela
                preview_window = tb.Toplevel(self)
                preview_window.title(f"Prévia do JSON - {d0.strftime('%d/%m/%Y')}")
                preview_window.geometry("900x700")
                
                # Adicionar stats no topo
                stats_frame = tb.Frame(preview_window)
                stats_frame.pack(fill=X, padx=8, pady=8)
                
                stats = [
                    f"📊 Estabelecimentos: {len(payload['estabelecimentos'])}",
                    f"👥 Clientes: {len(payload['clientes'])}",
                    f"📦 Produtos: {len(payload['produtos'])}",
                    f"💰 Vendas: {len(payload['vendas'])}",
                    f"🔄 Devoluções: {len(payload['vendasDevolucoesCancelamentos'])}",
                    f"📋 Estoque: {len(payload['estoque'])}"
                ]
                
                for i, stat in enumerate(stats):
                    tb.Label(stats_frame, text=stat, font=("Segoe UI", 9)).grid(row=i//3, column=i%3, padx=10, pady=2, sticky="w")
                
                # JSON Content
                content_frame = tb.Frame(preview_window)
                content_frame.pack(fill=BOTH, expand=YES, padx=8, pady=8)
                
                txt = ScrolledText(content_frame)
                txt.pack(fill=BOTH, expand=YES)
                txt.insert(END, beautify_json(payload))
                
                # Barra de botões
                btn_frame = tb.Frame(preview_window)
                btn_frame.pack(fill=X, padx=8, pady=8)
                
                # Adicionar botões
                tb.Button(btn_frame, text="Copiar JSON", 
                         command=lambda: self._copy_to_clipboard(beautify_json(payload), preview_window),
                         bootstyle="info").pack(side=LEFT, padx=5)
                
                tb.Button(btn_frame, text="Salvar como...", 
                         command=lambda: self._save_preview_json(payload),
                         bootstyle="success").pack(side=LEFT, padx=5)
                
                tb.Button(btn_frame, text="Fechar", 
                         command=preview_window.destroy,
                         bootstyle="secondary").pack(side=RIGHT, padx=5)
                
            finally:
                conn.close()
                
        except Exception as e:
            self._log(f"❌ Erro ao gerar prévia: {str(e)}")
            messagebox.showerror("Erro", str(e))
    
    def _copy_to_clipboard(self, text, parent_window=None):
        """Copia texto para a área de transferência"""
        self.clipboard_clear()
        self.clipboard_append(text)
        
        if parent_window:
            lbl = tb.Label(parent_window, text="✓ Copiado para a área de transferência!", 
                          bootstyle="success", font=("Segoe UI", 9))
            lbl.pack(side=BOTTOM, pady=5)
            parent_window.after(2000, lbl.destroy)
    
    def _save_preview_json(self, payload):
        """Salva o JSON de prévia em um arquivo"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Salvar prévia do JSON"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(beautify_json(payload))
            self._log(f"💾 Prévia salva em: {filename}")
    
    def _check_upload_status(self):
        """Verifica o status de um upload específico"""
        guid = self.guid_var.get().strip()
        if not guid:
            messagebox.showwarning("Aviso", "Informe o GUID do upload para verificar seu status.")
            return
        
        self.monitor_txt.delete(1.0, END)
        self.monitor_txt.insert(END, f"🔍 Verificando status do upload {guid}...\n")
        
        try:
            # Obter token primeiro
            token = get_token(
                self.cfg.iqvia_token_url, 
                self.cfg.iqvia_client_id, 
                self.cfg.iqvia_client_secret
            )
            
            if not token:
                self.monitor_txt.insert(END, "❌ Falha ao obter token de autenticação.\n")
                return
            
            # Obter URL base a partir da URL de upload
            base_url = self.cfg.iqvia_upload_url.rsplit('/', 1)[0]
            
            # Verificar status
            status = check_upload_status(base_url, guid, token)
            
            self.monitor_txt.insert(END, f"📊 Dados do upload {guid}:\n\n")
            self.monitor_txt.insert(END, beautify_json(status))
            
            # Salvar no histórico
            self._save_upload_history(guid, status)
            
        except Exception as e:
            self.monitor_txt.insert(END, f"❌ Erro ao verificar status: {str(e)}\n")
    
    def _save_upload_history(self, guid, status):
        """Salva o histórico de uploads para consultas futuras"""
        history_dir = Path(self.cfg.out_dir) / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        
        history_file = history_dir / "upload_history.json"
        
        # Carregar histórico existente
        history = {}
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        # Adicionar novo registro
        from datetime import datetime
        history[guid] = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status
        }
        
        # Salvar histórico
        history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _load_recent_uploads(self):
        """Carrega histórico de uploads recentes"""
        history_dir = Path(self.cfg.out_dir) / "history"
        history_file = history_dir / "upload_history.json"
        
        if not history_file.exists():
            self.monitor_txt.delete(1.0, END)
            self.monitor_txt.insert(END, "ℹ️ Nenhum histórico de uploads encontrado.\n")
            return
        
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
            
            self.monitor_txt.delete(1.0, END)
            self.monitor_txt.insert(END, "📜 Histórico de uploads recentes:\n\n")
            
            # Ordenar por timestamp mais recente
            sorted_guids = sorted(
                history.keys(),
                key=lambda k: history[k].get("timestamp", ""),
                reverse=True
            )
            
            for guid in sorted_guids[:10]:  # Mostrar apenas os 10 mais recentes
                entry = history[guid]
                timestamp = entry.get("timestamp", "Data desconhecida")
                status_data = entry.get("status", {})
                status = status_data.get("status", "Desconhecido")
                
                self.monitor_txt.insert(END, f"GUID: {guid}\n")
                self.monitor_txt.insert(END, f"Data: {timestamp}\n")
                self.monitor_txt.insert(END, f"Status: {status}\n")
                self.monitor_txt.insert(END, "-" * 50 + "\n")
            
        except Exception as e:
            self.monitor_txt.delete(1.0, END)
            self.monitor_txt.insert(END, f"❌ Erro ao carregar histórico: {str(e)}\n")
    
    def _show_version_history(self, event=None):
        """Exibe o histórico de versões do layout"""
        version_window = tb.Toplevel(self)
        version_window.title("Histórico de Versões do Layout")
        version_window.geometry("500x400")
        
        tb.Label(version_window, text="Histórico de Versões do Layout IQVIA", 
                font=("Segoe UI", 14, "bold")).pack(pady=(10,15))
        
        # Obter histórico de versões
        version_history = get_layout_changes()
        current_version = get_layout_version()
        
        # Exibir versão atual
        tb.Label(version_window, text=f"Versão atual: {current_version}", 
                font=("Segoe UI", 10, "bold")).pack(pady=(0,10))
        
        # Exibir histórico
        history_frame = tb.Frame(version_window)
        history_frame.pack(fill=BOTH, expand=YES, padx=20, pady=10)
        
        for i, (version, changes) in enumerate(version_history.items()):
            version_label = tb.Label(history_frame, text=f"v{version}", font=("Segoe UI", 10, "bold"))
            version_label.grid(row=i, column=0, sticky="nw", padx=(0,10), pady=(5,2))
            
            changes_label = tb.Label(history_frame, text=changes, wraplength=350, justify=LEFT)
            changes_label.grid(row=i, column=1, sticky="nw", pady=(5,2))
        
        # Botão para fechar
        tb.Button(version_window, text="Fechar", command=version_window.destroy,
                 bootstyle="secondary").pack(pady=15)


def run_app():
    App().mainloop()