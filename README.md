# GDDI – Gerador de dados IQVIA (Aurora BI)

## Como rodar
1. `pip install -r requirements.txt`
2. `python main.py`

## Pré-requisitos
- Oracle Instant Client instalado (pasta configurável na aba Configurações).
- Oracle 10g (modo thick) acessível.
- Credenciais IQVIA (Client ID/Secret).

## Fluxo
- Seleciona período (um JSON por dia).
- Gera ZIP único no final com nome `U_<CLIENTE>_<YYYYMMDD>_<YYYYMMDD>.zip`.
- Upload opcional para IQVIA (com retorno guid+md5).
- Validador leve de layout (opcional; pode apontar um JSON-exemplo oficial).

## Pastas
- `aurora_iqvia/` módulos internos.
- `assets/` (logo placeholder).
