# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Callable
from datetime import date, datetime
import io, zipfile, json

# Para execução direta
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports (relativos e absolutos)
try:
    from .db import AppConfig, connect_oracle, fetch_df
    from .sql_prisma import (
        SQL_MOV, SQL_DEVOLUCOES, SQL_FILIAL, SQL_CLIENTES,
        SQL_ESTOQUE, SQL_PRODUTOS_UNICOS, SQL_ENTRADA_PRODUTOS
    )
    from .utils import only_digits, md5_bytes, beautify_json, daterange
    from .iqvia_api import get_token, upload_zip
    from .validator import validate_payload, load_spec
except ImportError:
    from aurora_iqvia.db import AppConfig, connect_oracle, fetch_df
    from aurora_iqvia.sql_prisma import (
        SQL_MOV, SQL_DEVOLUCOES, SQL_FILIAL, SQL_CLIENTES,
        SQL_ESTOQUE, SQL_PRODUTOS_UNICOS, SQL_ENTRADA_PRODUTOS
    )
    from aurora_iqvia.utils import only_digits, md5_bytes, beautify_json, daterange
    from aurora_iqvia.iqvia_api import get_token, upload_zip
    from aurora_iqvia.validator import validate_payload, load_spec

# --------------------------
# Controle de versão do layout
# --------------------------
LAYOUT_VERSION = "1.0.3"

def get_layout_version():
    """Retorna a versão atual do layout"""
    return LAYOUT_VERSION

def get_layout_changes():
    """Retorna histórico de mudanças no layout"""
    return {
        "1.0.3": "Correção na estrutura de preços e brindes. Adicionado tratamento de descontos para brindes com preço de tabela exibido.",
        "1.0.2": "Adicionado campo tipoCaptacaoPrescricao nos estabelecimentos. Corrigido problema de 611 produtos faltantes no estoque.",
        "1.0.1": "Corrigido formato de série fiscal para STRING. Adicionada validação de layout.",
        "1.0.0": "Versão inicial do layout unificado IQVIA."
    }

# --------------------------
# Helpers de formatação
# --------------------------
def format_cep(cep: str) -> str:
    """
    Formata CEP conforme especificação IQVIA.
    
    Args:
        cep: String contendo o CEP com ou sem máscara
        
    Returns:
        String de 8 dígitos sem máscara e com zeros à esquerda
        
    Examples:
        >>> format_cep("12345-678")
        "12345678"
        >>> format_cep("1234")
        "00001234"
    """
    if not cep:
        return ""
    d = only_digits(cep).zfill(8)
    return d[:8]

def format_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ conforme especificação IQVIA.
    
    Args:
        cnpj: String contendo o CNPJ com ou sem máscara
        
    Returns:
        String de 14 dígitos sem máscara e com zeros à esquerda
        
    Examples:
        >>> format_cnpj("12.345.678/0001-99")
        "12345678000199"
        >>> format_cnpj("123456")
        "00000000123456"  # truncado para 14 dígitos
    """
    if not cnpj:
        return ""
    d = only_digits(cnpj).zfill(14)
    return d[:14]

def format_cpf(cpf: str) -> str:
    """
    Formata CPF conforme especificação IQVIA.
    
    Args:
        cpf: String contendo o CPF com ou sem máscara
        
    Returns:
        String de 11 dígitos sem máscara e com zeros à esquerda
        
    Examples:
        >>> format_cpf("123.456.789-00")
        "12345678900"
        >>> format_cpf("123456")
        "00000123456"
    """
    if not cpf:
        return ""
    d = only_digits(cpf).zfill(11)
    return d[:11]

def format_telefone(phone: str) -> str:
    """
    Formata telefone conforme especificação IQVIA.
    
    Args:
        phone: String contendo o telefone com ou sem máscara
        
    Returns:
        String apenas com dígitos
        
    Examples:
        >>> format_telefone("(11) 98765-4321")
        "11987654321"
        >>> format_telefone("")
        ""
    """
    if not phone:
        return ""
    return only_digits(phone)[:11]

def clean_text(text: str | None) -> str:
    """
    Limpa e normaliza texto, removendo caracteres problemáticos e corrigindo
    codificação de caracteres especiais.
    
    Args:
        text: String a ser limpa
        
    Returns:
        String limpa e normalizada
    """
    if not text:
        return ""
    try:
        if '�' in text or any(ord(c) > 1000 for c in text):
            text = text.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
    except:
        pass
    replacements = {
        'SÃ£O': 'SÃO', 'SÃƒO': 'SÃO', 'SÃ\x83O': 'SÃO',
        'Ã ': 'À','Ã¡': 'á','Ã¢':'â','Ã£':'ã','Ã¤':'ä','Ã§':'ç',
        'Ã©':'é','Ãª':'ê','Ã­':'í','Ã³':'ó','Ã´':'ô','Ãµ':'õ',
        'Ãº':'ú','Ã¼':'ü'
    }
    for k,v in replacements.items():
        text = text.replace(k, v)
    return " ".join(text.split())

def validate_field_length(value: str, max_length: int = 40) -> str:
    """
    Valida e trunca um valor para o tamanho máximo especificado.
    
    Args:
        value: String a ser validada
        max_length: Tamanho máximo permitido (default: 40)
        
    Returns:
        String limpa e truncada se necessário
    """
    if value is None:
        return ""
    s = clean_text(str(value))
    return s[:max_length] if len(s) > max_length else s

# --------------------------
# Payload
# --------------------------
def build_payload(
    mov, dev, fil, cli, est, produtos_unicos, dados_entrada,
    data_arquivo: date, client_id: str, codiqvia: str, logger: Callable[[str], None]
) -> Dict[str, Any]:
    """
    Constrói o payload JSON no formato IQVIA a partir dos dados extraídos.
    
    Args:
        mov: DataFrame com movimentações de vendas
        dev: DataFrame com devoluções
        fil: DataFrame com dados das filiais
        cli: DataFrame com dados dos clientes
        est: DataFrame com dados de estoque
        produtos_unicos: DataFrame com produtos únicos
        dados_entrada: Dicionário com dados complementares de entrada
        data_arquivo: Data de referência do arquivo
        client_id: ID do cliente na IQVIA
        codiqvia: Código IQVIA do estabelecimento
        logger: Função para log de mensagens
        
    Returns:
        Dicionário com o payload completo no formato IQVIA
    """

    # -------- Estabelecimentos --------
    logger("...dados das filiais")
    estabs: List[Dict[str, Any]] = []
    for r in fil.itertuples(index=False):
        tel_fil = format_telefone(getattr(r, "TELEFONE", "") or "")
        estabs.append({
            "cod": validate_field_length(str(r.CODFILIAL), 14),
            "doc": format_cnpj(getattr(r, "CGC", "") or ""),
            "nome": validate_field_length(getattr(r, "RAZAOSOCIAL", "") or "", 40),
            "nomeOfc": validate_field_length(getattr(r, "FANTASIA_FILIAL", "") or "", 40),
            "tipo": "CD",
            # Cosméticos: sem captação de prescrição
            "tipoCaptacaoPrescricao": 0,
            "ender": {
                "descr": validate_field_length(getattr(r, "ENDERECOFILIAL", "") or "", 70),
                "compl": "",  # ✅ CORRIGIDO: campo oficial, removido "num"
                "cep": format_cep(getattr(r, "CEP", "") or ""),
                "cidade": validate_field_length(getattr(r, "CIDADE", "") or "", 40) if hasattr(r, "CIDADE") else validate_field_length(getattr(r, "MUNICIPIO", "") or "", 40),
                "uf": validate_field_length(getattr(r, "UF", "") or "", 2),
                "tel": tel_fil,  # exigido pelo layout
            },
            "codIqvia": validate_field_length(str(codiqvia), 10)
        })

    # -------- Clientes --------
    logger("...dados dos clientes")
    clientes: List[Dict[str, Any]] = []
    for r in cli.itertuples(index=False):
        doc_raw = getattr(r, "CGCENT", "") or ""
        digits = only_digits(doc_raw)
        doc_fmt = format_cnpj(doc_raw) if len(digits) >= 12 else format_cpf(doc_raw)
        tel_cli = format_telefone(getattr(r, "TELENT", "") or "")
        # Cosméticos: não atuam com prof. saúde/prescrição
        tipo_cli = 2 if len(digits) == 14 else 1
        prof_saude = 0

        clientes.append({
            "cod": validate_field_length(str(getattr(r, "CODCLI", 0) or 0), 14),
            "doc": doc_fmt,
            "nome": validate_field_length(getattr(r, "CLIENTE", "") or "", 40),
            "nomeOfc": validate_field_length(getattr(r, "FANTASIA_CLIENT", "") or "", 40),
            "tipo": int(tipo_cli),
            "profSaude": int(prof_saude),
            "ender": {
                "descr": validate_field_length(getattr(r, "ENDERECOCLI", "") or "", 70),
                "compl": "",  # ✅ CORRIGIDO: campo oficial
                "cep": format_cep(getattr(r, "CEPENT", "") or ""),
                "cidade": validate_field_length(getattr(r, "MUNICENT", "") or "", 40),
                "uf": validate_field_length(getattr(r, "ESTENT", "") or "", 2),
                "tel": tel_cli,  # exigido pelo layout
            }
        })

    # -------- Produtos --------
    logger("...dados de produtos")
    dados_entrada = dados_entrada or {}
    produtos: List[Dict[str, Any]] = []
    for r in produtos_unicos.itertuples(index=False):
        ean_final = getattr(r, "CODAUXILIAR", "") or ""
        preco_final = round(float(getattr(r, "PTABELA", 0.0) or 0.0), 2)

        if getattr(r, "CODPROD", None) in dados_entrada:
            entrada = dados_entrada[r.CODPROD]
            if not ean_final and entrada.get('ean'):
                ean_final = str(entrada['ean'])
            if preco_final == 0.0 and entrada.get('preco'):
                preco_final = float(entrada['preco'])

        if ean_final:
            produtos.append({
                "cod": validate_field_length(str(r.CODPROD), 13),
                "eanSellIn": validate_field_length(str(ean_final), 14),
                "eanSellOut": validate_field_length(str(ean_final), 14),
                "ncm": validate_field_length(str(getattr(r, "NBM", "") or ""), 8),
                "apresent": validate_field_length(getattr(r, "DESCRICAO", "") or "", 70),
                "fabr": validate_field_length(getattr(r, "FORNECEDOR", "") or "", 40),
                "precoFabrica": round(preco_final, 2),
                # Cosméticos: não se aplica (strings conforme validador)
                "dispViaFarmaciaPopular": "0",
                "dispViaPbm": "0", 
                "marcaPropria": "0"
            })

    # -------- Vendas (apenas MOV) + brindes + campos extras de NF/pagto --------
    logger("...dados de vendas (incluindo brindes) - VERSÃO CORRIGIDA")
    vendas: List[Dict[str, Any]] = []
    for r in mov.itertuples(index=False):
        dt_s = r.DTSAIDA.strftime("%Y-%m-%d") if hasattr(r, "DTSAIDA") and hasattr(r.DTSAIDA, "strftime") else str(getattr(r, "DTSAIDA", ""))[:10]
        vl_unit = round(float(getattr(r, "PUNIT", 0.0) or 0.0), 2)

        eh_brinde = (vl_unit == 0.0) or (getattr(r, "BRINDE", "N") == "S")
        preco_para_json = vl_unit
        if eh_brinde and vl_unit == 0.0:
            preco_para_json = round(float(getattr(r, "PTABELA", 0.0) or 0.0), 2)

        # ✅ Campos extras corrigidos
        doc_tipo = 2 if (getattr(r, "CHAVENFE", None) not in (None, "", 0)) else 0
        doc_serie = str(int(getattr(r, "SERIE", 0) or 0))  # ✅ CORRIGIDO: STRING
        doc_num = int(getattr(r, "NUMNOTA", 0) or 0)
        danfe = str(getattr(r, "CHAVENFE", "") or "")
        venda_judic = 0
        tipo_pagto = 0

        venda = {
            "codEstab": validate_field_length(str(r.CODFILIAL), 14),
            "codCliente": validate_field_length(str(r.CODCLI), 14),
            # Cosméticos: sem prescrição / prof. saúde
            "comPrescricao": 0,
            "paraUsoProfSaude": 0,
            "codProfSaude": "0",
            "codProd": validate_field_length(str(r.CODPROD), 13),
            "dt": dt_s,
            "qt": int(getattr(r, "QT", 0) or 0),
            "ecommerce": 0,
            "meio": 5,  # 5 = Balcão (ajuste se necessário)
            # ✅ Campos de documento corrigidos:
            "docTipo": doc_tipo,
            "docFiscalSerie": doc_serie,     # ✅ STRING
            "docFiscalNum": doc_num,
            "danfe": danfe,
            "vendaJudic": venda_judic,
            "tipoPagto": tipo_pagto,
            # ✅ ESTRUTURA DE PREÇO CORRIGIDA
            "preco": {
                "valor": {                   # ✅ OBRIGATÓRIO - estava ausente
                    "liquido": preco_para_json,
                    "bruto": preco_para_json
                },
                "icms": {                    # ✅ DENTRO DE preco - estava fora
                    "isento": 0,
                    "aliq": round(float(getattr(r, "PERCICM", 0.0) or 0.0), 2),
                    "valor": round(float(getattr(r, "VLICMS", 0.0) or 0.0), 2),
                    "cst": str(getattr(r, "SITTRIBUT", "60") or "60"),
                    "subsTrib": {"valor": 0, "embutidoPreco": 0, "cest": "0"}
                }
            }
        }

        # ✅ Se for brinde, aplica desconto DENTRO de preco
        if eh_brinde:
            venda["preco"]["desconto"] = {
                "paraConsumidorFinal": 12,
                "perc": 100.00,
                "valor": preco_para_json
            }

        vendas.append(venda)

    # -------- Devoluções/Cancelamentos (APENAS DEV) - qt POSITIVA --------
    logger("...dados de devoluções/cancelamentos")
    vendas_devolucoes: List[Dict[str, Any]] = []
    for r in dev.itertuples(index=False):
        dt_s = r.DTSAIDA.strftime("%Y-%m-%d") if hasattr(r, "DTSAIDA") and hasattr(r.DTSAIDA, "strftime") else str(getattr(r, "DTSAIDA", ""))[:10]
        vendas_devolucoes.append({
            "codEstab": validate_field_length(str(r.CODFILIAL), 14),
            "codCliente": validate_field_length(str(r.CODCLI), 14),
            "codProfSaude": "0",
            "codProd": validate_field_length(str(r.CODPROD), 13),
            "comPrescricao": 0,
            "ecommerce": 0,
            "dt": dt_s,
            "qt": int(getattr(r, "QT", 0) or 0)  # POSITIVA
        })

    # -------- Estoque --------
    logger("...dados de estoque")
    estoque: List[Dict[str, Any]] = []
    for r in est.itertuples(index=False):
        ean_estoque = getattr(r, "CODAUXILIAR", "") or ""
        if not ean_estoque and hasattr(r, 'CODPROD') and r.CODPROD in (dados_entrada or {}):
            entrada_data = dados_entrada[r.CODPROD]
            if entrada_data.get('ean'):
                ean_estoque = str(entrada_data['ean'])

        if ean_estoque:
            estoque.append({
                "codEstab": validate_field_length(str(r.CODFILIAL), 14),
                "codProd": validate_field_length(str(r.CODPROD), 13),
                "dt": data_arquivo.strftime("%Y-%m-%d"),
                "qt": int(getattr(r, "ESTOQUEATUAL", 0) or 0)
            })

    # ✅ PAYLOAD COMPLETO COM SEÇÕES OBRIGATÓRIAS MÍNIMAS
    payload = {
        "data": data_arquivo.strftime("%Y-%m-%d"),
        "estabelecimentos": estabs,
        "clientes": clientes,
        "produtos": produtos,
        "vendas": vendas,
        "vendasDevolucoesCancelamentos": vendas_devolucoes,
        "estoque": estoque,
        # ✅ SEÇÕES VAZIAS MAS OBRIGATÓRIAS (evita erro na IQVIA)
        "profissionaisSaude": [],
        "pacientes": [],
        "fornecedores": [],
        "planosSaude": [],
        "laboratoriosPBM": [],
        "compras": [],
        "comprasDevolucoesCancelamentos": [],
        "prescricoes": []
    }
    return payload

# --------------------------
# Persistência (JSON/ZIP) e execução de período
# --------------------------
def save_json(payload: Dict[str, Any], client_id: str, dia: date, out_dir: Path) -> Path:
    """
    Salva payload como arquivo JSON.
    
    Args:
        payload: Dicionário com o payload
        client_id: ID do cliente
        dia: Data de referência 
        out_dir: Diretório de saída
        
    Returns:
        Path do arquivo salvo
    """
    name = f"U_{client_id.upper()}_{dia.strftime('%Y%m%d')}.json"
    fp = out_dir / name
    fp.write_text(beautify_json(payload), encoding="utf-8")
    return fp

def zip_period(json_paths: List[Path], client_id: str, out_dir: Path):
    """
    Cria arquivo ZIP com os JSONs do período.
    
    Args:
        json_paths: Lista de paths dos arquivos JSON
        client_id: ID do cliente
        out_dir: Diretório de saída
        
    Returns:
        Tuple com path do zip e MD5 do conteúdo
    """
    json_paths = sorted(json_paths, key=lambda p: p.name)
    ini = json_paths[0].stem[-8:]
    fim = json_paths[-1].stem[-8:]
    zip_name = f"U_{client_id.upper()}_{ini}_{fim}.zip"
    zip_path = out_dir / zip_name
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in json_paths:
            z.write(p, arcname=p.name)
    buf.seek(0)
    zip_path.write_bytes(buf.getvalue())
    return zip_path, md5_bytes(buf.getvalue())

def run_period(cfg: AppConfig, d0, d1, upload: bool, logger, validate: bool=False, example_layout: str=""):
    """
    Executa processamento para um período de datas.
    
    Args:
        cfg: Configuração da aplicação
        d0: Data inicial
        d1: Data final
        upload: Se deve fazer upload para IQVIA
        logger: Função para log
        validate: Se deve validar o JSON
        example_layout: Caminho para layout de exemplo
    """
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger(f"🔌 Conectando ao Oracle...")
    conn = connect_oracle(cfg)
    logger(f"✅ Conectado. DB version: {conn.version}")

    try:
        json_paths: List[Path] = []
        spec = load_spec(example_layout) if validate else None

        for dia in daterange(d0, d1):
            logger(f"📊 Processando dia {dia.strftime('%d/%m/%Y')}")

            logger("📄 Consultando movimentação de faturamento")
            mov = fetch_df(conn, SQL_MOV, DIA=dia, CODFILIAL=cfg.codfilial)

            logger("📄 Consultando devoluções")
            dev = fetch_df(conn, SQL_DEVOLUCOES, DIA=dia, CODFILIAL=cfg.codfilial)

            logger("🏢 Consultando filiais")
            fil = fetch_df(conn, SQL_FILIAL, DIA=dia, CODFILIAL=cfg.codfilial)

            logger("👥 Consultando clientes")
            cli = fetch_df(conn, SQL_CLIENTES, DIA=dia, CODFILIAL=cfg.codfilial)

            logger("📦 Consultando estoque")
            est = fetch_df(conn, SQL_ESTOQUE, DIA=dia, CODFILIAL=cfg.codfilial)

            logger("📥 Consultando dados de entrada para produtos sem EAN/preço")
            produtos_unicos = fetch_df(conn, SQL_PRODUTOS_UNICOS, DIA=dia, CODFILIAL=cfg.codfilial)
            entradas = fetch_df(conn, SQL_ENTRADA_PRODUTOS, DIA=dia, CODFILIAL=cfg.codfilial)

            dados_entrada = {}
            for r in entradas.itertuples(index=False):
                dados_entrada[int(getattr(r, "CODPROD"))] = {
                    "ean": getattr(r, "CODAUXILIAR", "") or "",
                    "preco": float(getattr(r, "PTABELA", 0.0) or 0.0)
                }

            payload = build_payload(
                mov, dev, fil, cli, est, produtos_unicos, dados_entrada,
                dia, cfg.iqvia_client_id, cfg.codiqvia, logger
            )

            # Validação leve opcional
            if validate and spec:
                errs = validate_payload(payload, spec)
                if errs:
                    logger("⚠️ Divergências encontradas na validação:")
                    for e in errs[:200]:
                        logger(" - " + e)
                else:
                    logger("✅ Payload válido segundo a spec")

            # Salvar JSON
            fp = save_json(payload, cfg.iqvia_client_id, dia, out_dir)
            logger(f"💾 JSON salvo: {fp.name}")

            json_paths.append(fp)

        if json_paths:
            logger("🗜️ Gerando ZIP do período...")
            zip_path, md5sum = zip_period(json_paths, cfg.iqvia_client_id, out_dir)
            logger(f"✅ ZIP gerado: {zip_path.name} (MD5: {md5sum})")

            if upload:
                logger("🌐 Autenticando na IQVIA...")
                tok = get_token(cfg.iqvia_token_url, cfg.iqvia_client_id, cfg.iqvia_client_secret, logger=logger)
                if not tok:
                    logger("❌ Falha ao obter token; upload cancelado.")
                else:
                    logger("📤 Enviando ZIP...")
                    resp = upload_zip(cfg.iqvia_upload_url, zip_path, tok, logger=logger)
                    logger("✅ Retorno IQVIA: " + json.dumps(resp, ensure_ascii=False))
                    
                    # Salvar histórico de uploads
                    try:
                        history_dir = out_dir / "history"
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
                        if 'guid' in resp:
                            history[resp['guid']] = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": resp,
                                "file": zip_path.name,
                                "period": f"{d0.strftime('%d/%m/%Y')} a {d1.strftime('%d/%m/%Y')}"
                            }
                            
                            # Salvar histórico
                            history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
                            logger(f"📝 Histórico de upload salvo: guid={resp['guid']}")
                    except Exception as e:
                        logger(f"⚠️ Erro ao salvar histórico: {str(e)}")
        else:
            logger("⚠️ Nenhum arquivo JSON foi gerado.")

        logger("✔️ Período concluído.")

    finally:
        try:
            conn.close()
        except Exception:
            pass

def diagnose_system(cfg: AppConfig, logger: Callable[[str], None]) -> List[str]:
    """
    Realiza diagnóstico do ambiente e dependências.
    
    Args:
        cfg: Configuração da aplicação
        logger: Função para log
        
    Returns:
        Lista de problemas encontrados
    """
    issues = []
    
    # Verificar Oracle Instant Client
    try:
        import oracledb
        version = oracledb.clientversion()
        logger(f"✅ Oracle Instant Client: {version}")
    except Exception as e:
        msg = f"❌ Problema com Oracle Instant Client: {str(e)}"
        logger(msg)
        issues.append(msg)
    
    # Verificar diretório de saída
    out_dir = Path(cfg.out_dir)
    if not out_dir.exists():
        msg = f"⚠️ Diretório de saída não existe: {out_dir}"
        logger(msg)
        issues.append(msg)
    else:
        try:
            # Tentar criar arquivo de teste
            test_file = out_dir / "__test_write.tmp"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()  # remover após teste
            logger(f"✅ Diretório de saída ({out_dir}) tem permissão de escrita")
        except Exception as e:
            msg = f"❌ Problema de permissão no diretório de saída: {str(e)}"
            logger(msg)
            issues.append(msg)
    
    # Verificar conectividade com IQVIA
    try:
        import requests
        r = requests.get("https://dataentry.solutions.iqvia.com/", timeout=5)
        if r.ok:
            logger("✅ Conectividade com IQVIA: OK")
        else:
            msg = f"⚠️ Problema de conectividade com IQVIA: HTTP {r.status_code}"
            logger(msg)
            issues.append(msg)
    except Exception as e:
        msg = f"❌ Erro ao testar conectividade com IQVIA: {str(e)}"
        logger(msg)
        issues.append(msg)
    
    # Verificar espaço em disco
    try:
        import shutil
        disk = shutil.disk_usage(str(out_dir))
        free_gb = disk.free / 1_000_000_000
        if free_gb < 1:  # Menos de 1GB livre
            msg = f"⚠️ Pouco espaço em disco: {free_gb:.2f}GB disponível"
            logger(msg)
            issues.append(msg)
        else:
            logger(f"✅ Espaço em disco: {free_gb:.2f}GB disponível")
    except Exception as e:
        logger(f"⚠️ Não foi possível verificar espaço em disco: {str(e)}")
    
    # Verificar dependências Python
    try:
        import pkg_resources
        required = {"ttkbootstrap", "requests", "pandas", "oracledb"}
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = required - installed
        
        if missing:
            msg = f"❌ Dependências faltando: {', '.join(missing)}"
            logger(msg)
            issues.append(msg)
        else:
            logger("✅ Todas as dependências Python estão instaladas")
    except Exception as e:
        logger(f"⚠️ Não foi possível verificar dependências: {str(e)}")
    
    return issues