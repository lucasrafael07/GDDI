# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Optional
import oracledb

CONFIG_FILE = Path(__file__).resolve().parent.parent / "iqvia_gui_config.json"

@dataclass
class AppConfig:
    # Oracle
    instant_client_dir: str = r"C:\iqvia_python\ClientLight\instantclient_23_8"
    db_host: str = "192.168.0.5"
    db_port: int = 1521
    db_sid: str = "WINT"
    db_user: str = "PRISMA"
    db_pass: str = "PRISMA"
    current_schema: str = "PRISMA"
    # IQVIA
    iqvia_client_id: str = "PRISMA_CD"
    iqvia_client_secret: str = "4X3O}bIpF6b6^<]n"
    iqvia_token_url: str = "https://dataentry.solutions.iqvia.com/api/v1/security/authenticate"
    iqvia_upload_url: str = "https://dataentry.solutions.iqvia.com/api/v1/layout1/upload"
    # App
    codfilial: int = 1
    codiqvia: str = "0892"
    out_dir: str = r"C:\iqvia_python\IQVIA_OUT"
    last_ini: str = ""
    last_fim: str = ""
    theme: str = "darkly"
    upload_default: bool = False
    # Validation
    validation_enabled: bool = True
    layout_example_path: str = ""

    def save(self):
        CONFIG_FILE.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def load() -> "AppConfig":
        if CONFIG_FILE.is_file():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return AppConfig(**data)
            except Exception:
                pass
        cfg = AppConfig()
        cfg.save()
        return cfg

def init_oracle_client(lib_dir: str):
    p = Path(lib_dir)
    if not p.exists():
        raise RuntimeError(f"Instant Client não encontrado: {p}")
    try:
        oracledb.init_oracle_client(lib_dir=str(p))
    except oracledb.ProgrammingError:
        # já inicializado
        pass

def connect_oracle(cfg: AppConfig):
    init_oracle_client(cfg.instant_client_dir)
    dsn = oracledb.makedsn(cfg.db_host, cfg.db_port, sid=cfg.db_sid)
    conn = oracledb.connect(user=cfg.db_user, password=cfg.db_pass, dsn=dsn)
    # tenta setar schema atual
    try:
        cur = conn.cursor()
        cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA={cfg.current_schema}")
        cur.close()
    except Exception:
        pass
    return conn

def test_connection(cfg: AppConfig) -> str:
    conn = connect_oracle(cfg)
    try:
        ver = conn.version
        return f"Conexão OK. Versão DB: {ver}"
    finally:
        conn.close()
