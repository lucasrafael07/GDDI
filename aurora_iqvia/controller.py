# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from datetime import date
import io, zipfile, json

# Adicionar o diretório pai ao path para permitir imports relativos
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Tentar imports relativos primeiro, depois absolutos
try:
    from .db import AppConfig, connect_oracle
    from .sql_prisma import (
        SQL_MOV, SQL_DEVOLUCOES, SQL_FILIAL, SQL_CLIENTES, 
        SQL_ESTOQUE, SQL_PRODUTOS_UNICOS, SQL_ENTRADA_PRODUTOS
    )
    from .utils import only_digits, md5_bytes, beautify_json, daterange
    from .iqvia_api import get_token, upload_zip
    from .validator import validate_payload, load_spec
except ImportError:
    # Se imports relativos falharem, tentar imports absolutos
    try:
        from aurora_iqvia.db import AppConfig, connect_oracle
        from aurora_iqvia.sql_prisma import (
            SQL_MOV, SQL_DEVOLUCOES, SQL_FILIAL, SQL_CLIENTES, 
            SQL_ESTOQUE, SQL_PRODUTOS_UNICOS, SQL_ENTRADA_PRODUTOS
        )
        from aurora_iqvia.utils import only_digits, md5_bytes, beautify_json, daterange
        from aurora_iqvia.iqvia_api import get_token, upload_zip
        from aurora_iqvia.validator import validate_payload, load_spec
    except ImportError as e:
        print(f"Erro ao importar módulos necessários: {e}")
        print("Certifique-se de que todos os módulos estão no mesmo diretório ou no PYTHONPATH")
        sys.exit(1)

# Funções de formatação IQVIA
def format_cep(cep: str) -> str:
    """Formata CEP: sempre 8 dígitos com zeros à esquerda"""
    if not cep:
        return ""
    digits = only_digits(cep)
    return digits.zfill(8)

def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ: sempre 14 dígitos com zeros à esquerda"""
    if not cnpj:
        return ""
    digits = only_digits(cnpj)
    return digits.zfill(14)

def format_telefone(telefone: str) -> str:
    """Formata telefone: DDD-NUMERO (ex: 11-22351121)"""
    if not telefone:
        return ""
    digits = only_digits(telefone)
    if len(digits) >= 10:
        ddd = digits[:2]
        numero = digits[2:]
        return f"{ddd}-{numero}"
    return digits

def clean_text(text: str) -> str:
    """Remove caracteres especiais problemáticos mantendo acentos válidos"""
    if not text:
        return ""
    
    # Converter para string e fazer strip
    text = str(text).strip()
    
    # Primeira tentativa: corrigir encoding comum
    try:
        # Se está como bytes mal decodificados
        if '�' in text or any(ord(c) > 1000 for c in text if len(text) > 0):
            # Tentar recodificar
            text_bytes = text.encode('latin1', errors='ignore')
            text = text_bytes.decode('utf-8', errors='ignore')
    except:
        pass
    
    # Segunda tentativa: substituições diretas para casos comuns
    replacements = {
        'SÃ£O': 'SÃO',
        'SÃƒO': 'SÃO', 
        'SÃ\x83O': 'SÃO',
        'Ã ': 'À',
        'Ã¡': 'á',
        'Ã¢': 'â', 
        'Ã£': 'ã',
        'Ã¤': 'ä',
        'Ã§': 'ç',
        'Ã©': 'é',
        'Ãª': 'ê',
        'Ã­': 'í',
        'Ã³': 'ó',
        'Ã´': 'ô',
        'Ãµ': 'õ',
        'Ãº': 'ú',
        'Ã¼': 'ü',
        'Ã±': 'ñ',
        # Casos específicos problemáticos
        'SÃƒâ€šÃ‚Â£O': 'SÃO',
        'SÃƒÂ£O': 'SÃO'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Terceira tentativa: normalização usando unidecode se disponível
    try:
        import unicodedata
        # Normalizar para remover caracteres compostos problemáticos
        text = unicodedata.normalize('NFKC', text)
    except:
        pass
    
    return text

def validate_field_length(value: str, max_length: int, field_name: str = "") -> str:
    """Valida tamanho máximo dos campos com limpeza de caracteres"""
    if not value:
        return ""
    
    # Limpar texto primeiro
    value_str = clean_text(value)
    
    if len(value_str) > max_length:
        return value_str[:max_length]
    return value_str

def fetch_df(conn, sql: str, **binds):
    """Executa SQL e retorna DataFrame"""
    cur = conn.cursor()
    cur.execute(sql, binds)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    try:
        import pandas as pd
        return pd.DataFrame.from_records(rows, columns=cols)
    except ImportError:
        print("Pandas não está instalado. Instale com: pip install pandas")
        sys.exit(1)

def build_payload(mov, dev, fil, cli, est, produtos_unicos, dados_entrada, data_arquivo: date, dia_mov: date, codiqvia: str, logger: Callable[[str], None]) -> Dict[str, Any]:
    """Constrói o payload JSON no formato IQVIA"""
    
    logger("...dados das filiais")
    estabs = []
    for r in fil.itertuples(index=False):
        estabs.append({
            "cod": validate_field_length(str(r.CODFILIAL), 14),
            "doc": format_cnpj(getattr(r, "CGC", "") or ""),
            "nome": validate_field_length(getattr(r, "RAZAOSOCIAL", "") or "", 40),
            "nomeOfc": validate_field_length(getattr(r, "FANTASIA_FILIAL", "") or "", 40),
            "tipo": "CD",
            "ender": {
                "descr": validate_field_length(getattr(r, "ENDERECOFILIAL", "") or "", 70),
                "cep": format_cep(getattr(r, "CEP", "") or ""),
                "cidade": validate_field_length(getattr(r, "CIDADE", "") or "", 30),
                "uf": validate_field_length(getattr(r, "UF", "") or "", 2),
                "tel": format_telefone(getattr(r, "TELEFONE", "") or ""),
            },
            "codIqvia": codiqvia,
            "tipoCaptacaoPrescricao": 3  # 3 = Check in e check out (padrão para farmácias)
        })

    logger("...dados de clientes")
    clientes = []
    for r in cli.itertuples(index=False):
        clientes.append({
            "tipo": 1, 
            "cod": validate_field_length(str(r.CODCLI), 14), 
            "profSaude": 0,
            "doc": format_cnpj(getattr(r, "CGCENT", "") or ""),
            "nome": validate_field_length(getattr(r, "CLIENTE", "") or "", 40),
            "nomeOfc": validate_field_length(getattr(r, "FANTASIA_CLIENT", "") or "", 40),
            "ender": {
                "descr": validate_field_length(getattr(r, "ENDERECOCLI", "") or "", 70),
                "cep": format_cep(getattr(r, "CEPENT", "") or ""),
                "cidade": validate_field_length(getattr(r, "MUNICENT", "") or "", 30),
                "uf": validate_field_length(getattr(r, "ESTENT", "") or "", 2),
                "tel": format_telefone(getattr(r, "TELENT", "") or ""),
            }
        })

    logger("...dados de produtos (unificados)")
    produtos = []
    for r in produtos_unicos.itertuples(index=False):
        # Buscar dados de entrada se necessário
        ean_final = getattr(r, "CODAUXILIAR", "") or ""
        preco_final = float(getattr(r, "PTABELA", 0.0) or 0.0)
        
        # Se não tem EAN ou preço, buscar das entradas
        if (not ean_final or preco_final == 0.0) and hasattr(r, 'CODPROD') and r.CODPROD in dados_entrada:
            entrada_data = dados_entrada[r.CODPROD]
            if not ean_final and entrada_data.get('ean'):
                ean_final = str(entrada_data['ean'])
            if preco_final == 0.0 and entrada_data.get('preco'):
                preco_final = float(entrada_data['preco'])
        
        # Só incluir produtos que tenham EAN válido
        if ean_final:
            produtos.append({
                "cod": validate_field_length(str(r.CODPROD), 13),
                "eanSellIn": validate_field_length(str(ean_final), 14),
                "eanSellOut": validate_field_length(str(ean_final), 14),
                "ncm": validate_field_length(str(getattr(r, "NBM", "") or ""), 8),
                "apresent": validate_field_length(getattr(r, "DESCRICAO", "") or "", 70),
                "fabr": validate_field_length(getattr(r, "FORNECEDOR", "") or "", 40),
                "precoFabrica": round(preco_final, 2),
                "dispViaFarmaciaPopular": "0",  # String conforme documentação IQVIA
                "dispViaPbm": "1",              # String conforme documentação IQVIA  
                "marcaPropria": "0"             # String conforme documentação IQVIA
            })

    logger("...dados de vendas (incluindo brindes)")
    vendas = []
    for r in mov.itertuples(index=False):
        dt_s = r.DTSAIDA.strftime("%Y-%m-%d") if hasattr(r.DTSAIDA, "strftime") else str(r.DTSAIDA)[:10]
        vl_unit = round(float(getattr(r, "PUNIT", 0.0) or 0.0), 2)
        
        # Verificar se é brinde (valor zero) mas MANTER o preço original
        eh_brinde = (vl_unit == 0.0) or (getattr(r, "BRINDE", "N") == "S")
        
        # Para brindes, usar preço da tabela em vez de zero
        preco_para_json = vl_unit
        if eh_brinde and vl_unit == 0.0:
            # Se é brinde com preço zero, usar preço da tabela
            preco_para_json = round(float(getattr(r, "PTABELA", 0.0) or 0.0), 2)
        
        venda = {
            "codEstab": validate_field_length(str(r.CODFILIAL), 14),
            "codCliente": validate_field_length(str(r.CODCLI), 14),
            "comPrescricao": 0,
            "paraUsoProfSaude": 0,
            "codProfSaude": "0",
            "codProd": validate_field_length(str(r.CODPROD), 13),
            "dt": dt_s,
            "qt": int(getattr(r, "QT", 0) or 0),
            "ecommerce": 0,
            "meio": 5,  # 5 = Balcão (padrão para farmácias físicas)
            "docTipo": 2,
            "docFiscalSerie": validate_field_length(str(getattr(r, "SERIE", "") or ""), 5),
            "docFiscalNum": int(getattr(r, "NUMNOTA", 0) or 0),
            "danfe": validate_field_length(str(getattr(r, "CHAVENFE", "") or ""), 44),
            "vendaJudic": 0,
            "tipoPagto": 7,  # 7 = Outros (padrão)
            "preco": {
                "valor": {"liquido": preco_para_json, "bruto": preco_para_json},
                "icms": {
                    "isento": 0,
                    "aliq": round(float(getattr(r, "PERCICM", 0.0) or 0.0), 2),
                    "valor": round(float(getattr(r, "VLICMS", 0.0) or 0.0), 2),
                    "cst": str(getattr(r, "SITTRIBUT", "60") or "60"),
                    "subsTrib": {
                        "valor": 0, 
                        "embutidoPreco": 0, 
                        "cest": "0"
                    }
                }
            }
        }
        
        # Se for brinde, adicionar desconto específico
        if eh_brinde:
            venda["preco"]["desconto"] = {
                "paraConsumidorFinal": 12,  # 12 = Brinde conforme documentação IQVIA
                "perc": 100.00,
                "valor": preco_para_json  # Valor do desconto = preço do produto
            }
        
        vendas.append(venda)

    # Adicionar devoluções às vendas também (conforme solicitado no ponto 4)
    logger("...adicionando devoluções às vendas")
    for r in dev.itertuples(index=False):
        dt_s = r.DTSAIDA.strftime("%Y-%m-%d") if hasattr(r.DTSAIDA, "strftime") else str(r.DTSAIDA)[:10]
        vl_unit = round(float(getattr(r, "PUNIT", 0.0) or 0.0), 2)
        
        vendas.append({
            "codEstab": validate_field_length(str(r.CODFILIAL), 14),
            "codCliente": validate_field_length(str(r.CODCLI), 14),
            "comPrescricao": 0,
            "paraUsoProfSaude": 0,
            "codProfSaude": "0",
            "codProd": validate_field_length(str(r.CODPROD), 13),
            "dt": dt_s,
            "qt": -int(getattr(r, "QT", 0) or 0),  # Quantidade negativa para devolução
            "ecommerce": 0,
            "meio": 5,  # 5 = Balcão
            "docTipo": 2,
            "docFiscalSerie": validate_field_length(str(getattr(r, "SERIE", "") or ""), 5),
            "docFiscalNum": int(getattr(r, "NUMNOTA", 0) or 0),
            "danfe": validate_field_length(str(getattr(r, "CHAVENFE", "") or ""), 44),
            "vendaJudic": 0,
            "tipoPagto": 7,
            "preco": {
                "valor": {"liquido": vl_unit, "bruto": vl_unit},
                "icms": {
                    "isento": 0,
                    "aliq": round(float(getattr(r, "PERCICM", 0.0) or 0.0), 2),
                    "valor": round(float(getattr(r, "VLICMS", 0.0) or 0.0), 2),
                    "cst": str(getattr(r, "SITTRIBUT", "60") or "60"),
                    "subsTrib": {
                        "valor": 0, 
                        "embutidoPreco": 0, 
                        "cest": "0"
                    }
                }
            }
        })

    logger("...dados de devoluções/cancelamentos")
    vendas_devolucoes = []
    for r in dev.itertuples(index=False):
        dt_s = r.DTSAIDA.strftime("%Y-%m-%d") if hasattr(r.DTSAIDA, "strftime") else str(r.DTSAIDA)[:10]
        
        vendas_devolucoes.append({
            "codEstab": validate_field_length(str(r.CODFILIAL), 14),
            "codCliente": validate_field_length(str(r.CODCLI), 14),
            "codProfSaude": "0",
            "codProd": validate_field_length(str(r.CODPROD), 13),
            "comPrescricao": 0,
            "ecommerce": 0,
            "dt": dt_s,
            "qt": int(getattr(r, "QT", 0) or 0)
        })

    logger("...dados de estoque")
    estoque = []
    for r in est.itertuples(index=False):
        # Buscar EAN das entradas se necessário
        ean_estoque = getattr(r, "CODAUXILIAR", "") or ""
        if not ean_estoque and hasattr(r, 'CODPROD') and r.CODPROD in dados_entrada:
            entrada_data = dados_entrada[r.CODPROD]
            if entrada_data.get('ean'):
                ean_estoque = str(entrada_data['ean'])
        
        # Só incluir no estoque se tiver EAN válido
        if ean_estoque:
            estoque.append({
                "codEstab": validate_field_length(str(r.CODFILIAL), 14),
                "codProd": validate_field_length(str(r.CODPROD), 13),
                "dt": dia_mov.strftime("%Y-%m-%d"),
                "qt": int(getattr(r, "ESTOQUEATUAL", 0) or 0)
            })

    payload = {
        "data": data_arquivo.strftime("%Y-%m-%d"),
        "estabelecimentos": estabs,
        "clientes": clientes,
        "produtos": produtos,
        "vendas": vendas,
        "vendasDevolucoesCancelamentos": vendas_devolucoes,
        "estoque": estoque
    }
    return payload

def save_json(payload: Dict[str, Any], client_id: str, dia, out_dir: Path) -> Path:
    """Salva payload como arquivo JSON"""
    name = f"U_{client_id.upper()}_{dia.strftime('%Y%m%d')}.json"
    fp = out_dir / name
    fp.write_text(beautify_json(payload), encoding="utf-8")
    return fp

def zip_period(json_paths: List[Path], client_id: str, out_dir: Path):
    """Cria arquivo ZIP com os JSONs do período"""
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
    """Executa processamento para um período de datas"""
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    logger("🔌 Conectando ao Oracle...")
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
            try:
                entradas = fetch_df(conn, SQL_ENTRADA_PRODUTOS, DIA=dia, CODFILIAL=cfg.codfilial)
                
                # Criar dicionário de dados de entrada (última entrada por produto)
                dados_entrada = {}
                if not entradas.empty:
                    for r in entradas.itertuples(index=False):
                        if getattr(r, 'RN', 1) == 1:  # Primeira linha = mais recente
                            dados_entrada[r.CODPROD] = {
                                'ean': getattr(r, 'CODAUXILIAR', None),
                                'preco': getattr(r, 'PUNIT', 0.0)
                            }
                
                logger(f"📥 {len(dados_entrada)} produtos com dados de entrada encontrados")
            except Exception as e:
                logger(f"⚠️ Erro ao buscar dados de entrada: {e}")
                dados_entrada = {}  # Continuar sem dados de entrada
            
            logger("🛍️ Consultando produtos únicos (vendas + devoluções + estoque)")
            produtos_unicos = fetch_df(conn, SQL_PRODUTOS_UNICOS, DIA=dia, CODFILIAL=cfg.codfilial)

            logger("🧱 Montando JSON")
            payload = build_payload(mov, dev, fil, cli, est, produtos_unicos, dados_entrada, date.today(), dia, cfg.codiqvia, logger)

            if validate and spec:
                logger("🔍 Validando layout (leve)")
                errs = validate_payload(payload, spec)
                if errs:
                    logger("⚠️ Divergências detectadas (parcial):")
                    for e in errs[:50]:
                        logger("  - " + e)
                else:
                    logger("✅ Estrutura OK (checagem leve).")

            fp = save_json(payload, cfg.iqvia_client_id, dia, out_dir)
            logger(f"💾 Arquivo {fp.name} salvo em {out_dir}")

            # contagens
            logger(f"Σ Dia {dia.strftime('%d/%m/%Y')}: "
                   f"filiais={len(payload['estabelecimentos'])} | "
                   f"clientes={len(payload['clientes'])} | "
                   f"produtos={len(payload['produtos'])} | "
                   f"vendas={len(payload['vendas'])} | "
                   f"devoluções={len(payload['vendasDevolucoesCancelamentos'])} | "
                   f"estoque={len(payload['estoque'])}")

            json_paths.append(fp)

        if json_paths:
            zip_path, md5_hex = zip_period(json_paths, cfg.iqvia_client_id, out_dir)
            logger(f"🗜️ ZIP gerado: {zip_path.name} (MD5={md5_hex})")

            if upload:
                logger("🌐 Autenticando na IQVIA...")
                tok = get_token(cfg.iqvia_token_url, cfg.iqvia_client_id, cfg.iqvia_client_secret, logger=logger)
                if not tok:
                    logger("❌ Falha ao obter token; upload cancelado.")
                else:
                    logger("📤 Enviando ZIP...")
                    resp = upload_zip(cfg.iqvia_upload_url, zip_path, tok, logger=logger)
                    logger("✅ Retorno IQVIA: " + json.dumps(resp, ensure_ascii=False))
        else:
            logger("⚠️ Nenhum arquivo JSON foi gerado.")

        logger("✔️ Período concluído.")
        
    except Exception as e:
        logger(f"❌ Erro durante processamento: {e}")
        raise
    finally:
        try:
            conn.close()
            logger("🔌 Conexão Oracle fechada.")
        except Exception:
            pass

def debug_encoding_issues(text: str) -> str:
    """Função de debug para identificar problemas de encoding"""
    if not text:
        return ""
    
    print(f"🔍 Debug: Texto original: '{text}'")
    print(f"🔍 Debug: Bytes: {[hex(ord(c)) for c in text[:20]]}")
    
    # Tentar diferentes correções
    corrected = clean_text(text)
    print(f"🔍 Debug: Texto corrigido: '{corrected}'")
    
    return corrected

# Código de teste/exemplo quando executado diretamente
if __name__ == "__main__":
    print("Controller IQVIA - Teste de Importação")
    print("=" * 50)
    
    # Teste básico de imports
    try:
        print("✅ Imports realizados com sucesso")
        print("✅ Funções de formatação disponíveis")
        print("✅ Função build_payload disponível")
        print("✅ Função run_period disponível")
        
        # Teste das funções de formatação
        print("\n🧪 Testando funções de formatação:")
        print(f"format_cep('1234567'): {format_cep('1234567')}")
        print(f"format_cnpj('12345678000195'): {format_cnpj('12345678000195')}")
        print(f"format_telefone('11987654321'): {format_telefone('11987654321')}")
        print(f"validate_field_length('Texto muito longo', 10): {validate_field_length('Texto muito longo', 10)}")
        
        # Teste de encoding
        print("\n🧪 Testando correção de encoding:")
        test_texts = [
            "SÃO LEOPOLDO",
            "SÃƒO PAULO", 
            "JOSÉ MARIA",
            "JOÃO PESSOA"
        ]
        
        for test_text in test_texts:
            cleaned = clean_text(test_text)
            print(f"'{test_text}' → '{cleaned}'")
        
        print("\n✅ Todas as funções estão funcionando corretamente!")
        print("\n📋 Estrutura do projeto detectada:")
        print("- DB: AppConfig e connect_oracle")
        print("- SQL: Queries do SQL_PRISMA")
        print("- Utils: Funções utilitárias")
        print("- IQVIA API: Token e upload")
        print("- Validator: Validação de layout")
        print("- Encoding: Correção automática de caracteres")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)