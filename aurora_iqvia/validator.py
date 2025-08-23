# -*- coding: utf-8 -*-
"""
Validador simples para o layout IQVIA.
- Se houver um arquivo de layout JSON oficial (exemplo), ele é lido e usado para conferir chaves de 1º nível.
- Caso contrário, aplica uma especificação interna mínima (fallback) apenas nos campos já usados.
- Apenas acusa divergências: não altera o payload.
"""

from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json

FALLBACK_SPEC = {
    "data": "str",
    "estabelecimentos": [{
        "cod": "str", "doc": "str", "nome": "str", "nomeOfc": "str", "tipo": "str",
        "ender": {"descr":"str","cep":"str","cidade":"str","uf":"str","tel":"str"},
        "codIqvia": "str", "tipoCaptacaoPrescricao": "int"
    }],
    "clientes": [{
        "tipo":"int","cod":"str","profSaude":"int","doc":"str","nome":"str","nomeOfc":"str",
        "ender":{"descr":"str","cep":"str","cidade":"str","uf":"str","tel":"str"}
    }],
    "produtos": [{
        "cod":"str","eanSellIn":"str","eanSellOut":"str","ncm":"str","apresent":"str","fabr":"str",
        "precoFabrica":"float","dispViaFarmaciaPopular":"str","dispViaPbm":"str","marcaPropria":"str"
    }],
    "vendas": [{
        "codEstab":"str","codCliente":"str","comPrescricao":"int","paraUsoProfSaude":"int","codProfSaude":"str",
        "codProd":"str","dt":"str","qt":"int","ecommerce":"int","meio":"int","docTipo":"int",
        "docFiscalSerie":"str","docFiscalNum":"int","danfe":"str","vendaJudic":"int","tipoPagto":"int",
        "preco":{"valor":{"liquido":"float","bruto":"float"},
                 "icms":{"isento":"int","aliq":"float","valor":"float","cst":"str",
                         "subsTrib":{"valor":"int","embutidoPreco":"int","cest":"str"}}}
    }],
    "estoque": [{"codEstab":"str","codProd":"str","dt":"str","qt":"int"}]
}

def load_spec(path: str | None) -> Dict[str, Any]:
    if path:
        p = Path(path)
        if p.is_file():
            try:
                # O "layout JSON exemplo" da IQVIA é um arquivo payload.
                # Para fins de validação, extraímos apenas chaves do 1º nível.
                sample = json.loads(p.read_text(encoding="utf-8"))
                spec = {
                    "data": "str",
                    "estabelecimentos": [{}],
                    "clientes": [{}],
                    "produtos": [{}],
                    "vendas": [{}],
                    "estoque": [{}]
                }
                # Não inferimos tipos profundos do exemplo; mantemos checagem leve.
                return spec
            except Exception:
                pass
    return FALLBACK_SPEC

def _type_ok(value: Any, tname: str) -> bool:
    if tname == "str":
        return isinstance(value, str)
    if tname == "int":
        return isinstance(value, int)
    if tname == "float":
        return isinstance(value, (int, float))
    if tname == "list":
        return isinstance(value, list)
    if tname == "dict":
        return isinstance(value, dict)
    return True

def _validate_obj(obj: Any, spec: Any, path: str, errs: List[str]):
    # spec may be dict, list-pattern (with single dict inside) or type name
    if isinstance(spec, dict):
        if not isinstance(obj, dict):
            errs.append(f"{path}: esperado objeto, obtido {type(obj).__name__}")
            return
        for k, sub_spec in spec.items():
            if k not in obj:
                errs.append(f"{path}.{k}: campo obrigatório ausente")
                continue
            _validate_obj(obj[k], sub_spec, f"{path}.{k}", errs)
    elif isinstance(spec, list):
        if not isinstance(obj, list):
            errs.append(f"{path}: esperado lista, obtido {type(obj).__name__}")
            return
        # caso de lista homogênea: spec[0] é o "molde"
        tmpl = spec[0] if spec else None
        if tmpl is not None:
            for i, item in enumerate(obj[:2000]):  # limita para não estourar log
                _validate_obj(item, tmpl, f"{path}[{i}]", errs)
    elif isinstance(spec, str):
        if not _type_ok(obj, spec):
            errs.append(f"{path}: tipo esperado {spec}, obtido {type(obj).__name__}")
    else:
        # desconhecido: ignora
        pass

def validate_payload(payload: Dict[str, Any], spec: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    # Campos de 1º nível obrigatórios
    for key in ["data","estabelecimentos","clientes","produtos","vendas","estoque"]:
        if key not in payload:
            errs.append(f"$.{key}: ausente")
    # Validação leve por spec
    _validate_obj(payload, spec, "$", errs)
    return errs