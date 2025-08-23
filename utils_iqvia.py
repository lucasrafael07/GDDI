# -*- coding: utf-8 -*-
"""
Funções utilitárias para formatação conforme documentação IQVIA
"""

import re
from typing import Optional

def format_cep(cep: str) -> str:
    """
    Formata CEP conforme documentação IQVIA:
    "Sempre 8 dígitos preenchidos com zeros à esquerda e sem máscara"
    """
    if not cep:
        return ""
    digits = only_digits(cep)
    return digits.zfill(8)

def format_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ conforme documentação IQVIA:
    "CNPJ sempre 14 dígitos preenchidos com zeros à esquerda e sem máscara"
    """
    if not cnpj:
        return ""
    digits = only_digits(cnpj)
    return digits.zfill(14)

def format_telefone(telefone: str) -> str:
    """
    Formata telefone conforme documentação IQVIA:
    "<<DDD com dois dígitos>> + \"-\" + <<número do telefone sem máscara>>"
    Exemplo: "11-22351121"
    """
    if not telefone:
        return ""
    
    digits = only_digits(telefone)
    
    # Se tem 10 ou 11 dígitos, assumir que primeiros 2 são DDD
    if len(digits) >= 10:
        ddd = digits[:2]
        numero = digits[2:]
        return f"{ddd}-{numero}"
    
    # Se tem menos de 10 dígitos, retornar sem formatação DDD
    return digits

def format_crm(documento: str, uf: str) -> str:
    """
    Formata documento profissional conforme documentação IQVIA:
    "<<sigla da entidade>> + <<número com 9 dígitos zeros à esquerda>> + <<UF>>"
    Exemplo: "CRM000091475SP"
    """
    if not documento:
        return ""
    
    # Extrair sigla, número e UF do documento
    match = re.match(r'^([A-Z]{3})(\d+)([A-Z]{2})?', documento.upper())
    
    if match:
        sigla = match.group(1)
        numero = match.group(2).zfill(9)  # 9 dígitos com zeros à esquerda
        uf_doc = match.group(3) or uf.upper()
        return f"{sigla}{numero}{uf_doc}"
    
    return documento

def format_decimal_2_casas(valor) -> str:
    """
    Formata decimal conforme documentação IQVIA:
    "Sempre com duas casas decimais, separadas por ponto (.)"
    """
    if valor is None:
        return "0.00"
    
    try:
        return f"{float(valor):.2f}"
    except (ValueError, TypeError):
        return "0.00"

def format_endereco(logradouro: str, numero: str) -> str:
    """
    Formata endereço conforme documentação IQVIA:
    "<<tipo do logradouro>> + \" \" + <<logradouro>> + \", \" + <<número no logradouro>>"
    """
    if not logradouro:
        return ""
    
    endereco = logradouro.strip()
    if numero and numero.strip():
        if not endereco.endswith(','):
            endereco += ","
        endereco += f" {numero.strip()}"
    
    return endereco

def get_tipo_pagamento_codigo(tipo_descricao: str) -> int:
    """
    Converte descrição do tipo de pagamento para código IQVIA
    """
    tipos = {
        'dinheiro': 1,
        'cartao_credito': 2,
        'cartao_debito': 3,
        'cheque': 4,
        'boleto': 5,
        'paypal': 6,
        'outros': 7
    }
    
    return tipos.get(tipo_descricao.lower(), 7)  # Default: outros

def get_meio_venda_codigo(meio_descricao: str) -> int:
    """
    Converte descrição do meio de venda para código IQVIA
    """
    meios = {
        'app_proprio': 1,
        'site_proprio': 2,
        'ifood': 31,
        'rappi': 32,
        'uber_eats': 33,
        'marketplace': 4,
        'balcao': 5,
        'televendas': 71,
        'whatsapp': 72,
        'memed': 81,
        'outros': 9
    }
    
    return meios.get(meio_descricao.lower(), 5)  # Default: balcão

def get_tipo_desconto_brinde() -> dict:
    """
    Retorna estrutura de desconto para brindes conforme documentação IQVIA
    """
    return {
        "paraConsumidorFinal": 12,  # 12 = Brinde
        "perc": 100.00,
        "valor": 0.00
    }

def validate_field_length(value: str, max_length: int, field_name: str = "") -> str:
    """
    Valida e trunca campo conforme tamanho máximo da documentação IQVIA
    """
    if not value:
        return ""
    
    value_str = str(value).strip()
    if len(value_str) > max_length:
        print(f"⚠️ Campo {field_name} truncado de {len(value_str)} para {max_length} caracteres")
        return value_str[:max_length]
    
    return value_str

def only_digits(s: str) -> str:
    """
    Extrai apenas dígitos de uma string
    """
    if not s:
        return ""
    return "".join(ch for ch in str(s) if ch.isdigit())

# Tamanhos máximos conforme documentação IQVIA
TAMANHOS_CAMPOS = {
    'estabelecimentos': {
        'cod': 14,
        'doc': 14,
        'nome': 40,
        'nomeOfc': 40,
        'tipo': 3,
        'ender_descr': 70,
        'ender_compl': 20,
        'ender_cep': 8,
        'ender_cidade': 30,
        'ender_uf': 2,
        'ender_tel': 20,
        'codIqvia': 4
    },
    'produtos': {
        'cod': 13,
        'eanSellIn': 14,
        'eanSellOut': 14,
        'qrcode': 500,
        'ncm': 8,
        'apresent': 70,
        'fabr': 40,
        'molecula': 100
    },
    'clientes': {
        'cod': 14,
        'doc': 14,
        'nome': 40,
        'nomeOfc': 40,
        'ender_descr': 70,
        'ender_compl': 20,
        'ender_cep': 8,
        'ender_cidade': 30,
        'ender_uf': 2,
        'ender_tel': 20
    }
}

def validate_estabelecimento_fields(estab: dict) -> dict:
    """
    Valida e formata campos de estabelecimento conforme documentação IQVIA
    """
    tamanhos = TAMANHOS_CAMPOS['estabelecimentos']
    
    return {
        'cod': validate_field_length(estab.get('cod', ''), tamanhos['cod'], 'estabelecimento.cod'),
        'doc': format_cnpj(estab.get('doc', '')),
        'nome': validate_field_length(estab.get('nome', ''), tamanhos['nome'], 'estabelecimento.nome'),
        'nomeOfc': validate_field_length(estab.get('nomeOfc', ''), tamanhos['nomeOfc'], 'estabelecimento.nomeOfc'),
        'tipo': validate_field_length(estab.get('tipo', 'CD'), tamanhos['tipo'], 'estabelecimento.tipo'),
        'ender': {
            'descr': validate_field_length(estab.get('ender', {}).get('descr', ''), tamanhos['ender_descr'], 'ender.descr'),
            'compl': validate_field_length(estab.get('ender', {}).get('compl', ''), tamanhos['ender_compl'], 'ender.compl'),
            'cep': format_cep(estab.get('ender', {}).get('cep', '')),
            'cidade': validate_field_length(estab.get('ender', {}).get('cidade', ''), tamanhos['ender_cidade'], 'ender.cidade'),
            'uf': validate_field_length(estab.get('ender', {}).get('uf', ''), tamanhos['ender_uf'], 'ender.uf'),
            'tel': format_telefone(estab.get('ender', {}).get('tel', ''))
        },
        'codIqvia': validate_field_length(str(estab.get('codIqvia', '')), tamanhos['codIqvia'], 'codIqvia'),
        'tipoCaptacaoPrescricao': int(estab.get('tipoCaptacaoPrescricao', 1))
    }

def validate_produto_fields(produto: dict) -> dict:
    """
    Valida e formata campos de produto conforme documentação IQVIA
    """
    tamanhos = TAMANHOS_CAMPOS['produtos']
    
    return {
        'cod': validate_field_length(produto.get('cod', ''), tamanhos['cod'], 'produto.cod'),
        'eanSellIn': validate_field_length(produto.get('eanSellIn', ''), tamanhos['eanSellIn'], 'produto.eanSellIn'),
        'eanSellOut': validate_field_length(produto.get('eanSellOut', ''), tamanhos['eanSellOut'], 'produto.eanSellOut'),
        'qrcode': validate_field_length(produto.get('qrcode', ''), tamanhos['qrcode'], 'produto.qrcode'),
        'ncm': validate_field_length(produto.get('ncm', ''), tamanhos['ncm'], 'produto.ncm'),
        'apresent': validate_field_length(produto.get('apresent', ''), tamanhos['apresent'], 'produto.apresent'),
        'fabr': validate_field_length(produto.get('fabr', ''), tamanhos['fabr'], 'produto.fabr'),
        'molecula': validate_field_length(produto.get('molecula', ''), tamanhos['molecula'], 'produto.molecula'),
        'precoFabrica': float(produto.get('precoFabrica', 0.0)),
        'dispViaFarmaciaPopular': int(produto.get('dispViaFarmaciaPopular', 0)),
        'dispViaPbm': int(produto.get('dispViaPbm', 0)),
        'marcaPropria': int(produto.get('marcaPropria', 0))
    }