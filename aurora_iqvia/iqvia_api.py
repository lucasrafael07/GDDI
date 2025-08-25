# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Dict, Any
import requests

def _looks_like_jwt(s: str) -> bool:
    """
    Verifica se uma string parece ser um token JWT válido.
    
    Args:
        s: String a ser verificada
        
    Returns:
        True se parece um JWT, False caso contrário
    """
    if not isinstance(s, str):
        return False
    parts = s.strip().split(".")
    return len(parts) == 3 and all(parts)

def get_token(token_url: str, client_id: str, client_secret: str, logger=print, timeout=60) -> Optional[str]:
    """
    Obtém token de autenticação da IQVIA.
    
    Args:
        token_url: URL para obtenção de token
        client_id: ID do cliente
        client_secret: Secret do cliente
        logger: Função para log
        timeout: Timeout da requisição em segundos
        
    Returns:
        Token JWT ou None se falhar
    """
    payload = {"client_id": client_id.lower(), "client_secret": client_secret}
    # Tentativa JSON
    try:
        r = requests.post(token_url, json=payload, headers={"Content-Type":"application/json"}, timeout=timeout)
        if r.ok:
            try:
                j = r.json()
                tok = j.get("access_token") or j.get("token") or j.get("jwt") or j.get("bearerToken")
                if tok:
                    logger("✅ Token obtido (JSON).")
                    return tok
            except Exception:
                pass
            if _looks_like_jwt(r.text.strip()):
                logger("✅ Token obtido (JWT puro).")
                return r.text.strip()
        else:
            logger(f"⚠️ Token JSON falhou: {r.status_code} {r.text[:200]}")
    except Exception as e:
        logger(f"⚠️ Erro tentativa JSON: {e}")

    # Tentativa x-www-form-urlencoded
    try:
        r2 = requests.post(token_url, data=payload,
                           headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=timeout)
        if r2.ok:
            try:
                j2 = r2.json()
                tok2 = j2.get("access_token") or j2.get("token") or j2.get("jwt") or j2.get("bearerToken")
                if tok2:
                    logger("✅ Token obtido (form).")
                    return tok2
            except Exception:
                pass
            if _looks_like_jwt(r2.text.strip()):
                logger("✅ Token obtido (JWT puro - form).")
                return r2.text.strip()
        else:
            logger(f"⚠️ Token form falhou: {r2.status_code} {r2.text[:200]}")
    except Exception as e:
        logger(f"⚠️ Erro tentativa form: {e}")
    return None

def upload_zip(upload_url: str, zip_path, token: str, logger=print) -> Dict[str, Any]:
    """
    Faz upload de arquivo ZIP para a IQVIA.
    
    Args:
        upload_url: URL para upload
        zip_path: Caminho do arquivo ZIP
        token: Token de autenticação
        logger: Função para log
        
    Returns:
        Resposta da API em formato dict
    """
    headers = {"Authorization": f"Bearer {token}"}
    with open(zip_path, "rb") as f:
        files = {"file": (zip_path.name, f, "application/zip")}
        r = requests.post(upload_url, headers=headers, files=files, timeout=180)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}

def check_upload_status(upload_url_base: str, guid: str, token: str) -> Dict[str, Any]:
    """
    Verifica o status de um upload anterior.
    
    Args:
        upload_url_base: URL base da API (sem o endpoint final)
        guid: GUID do upload a ser verificado
        token: Token de autenticação
        
    Returns:
        Status do upload em formato dict
    """
    status_url = f"{upload_url_base}/status/{guid}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        r = requests.get(status_url, headers=headers, timeout=30)
        if r.ok:
            try:
                return r.json()
            except Exception:
                return {"status": "success", "raw": r.text}
        return {"status": "error", "message": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao verificar status: {str(e)}"}

def test_comm(token_url: str, client_id: str, client_secret: str, logger=print) -> bool:
    """
    Testa comunicação com a IQVIA.
    
    Args:
        token_url: URL para obtenção de token
        client_id: ID do cliente
        client_secret: Secret do cliente
        logger: Função para log
        
    Returns:
        True se comunicação OK, False caso contrário
    """
    tok = get_token(token_url, client_id, client_secret, logger=logger)
    return tok is not None