# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Dict, Any
import requests

def _looks_like_jwt(s: str) -> bool:
    if not isinstance(s, str):
        return False
    parts = s.strip().split(".")
    return len(parts) == 3 and all(parts)

def get_token(token_url: str, client_id: str, client_secret: str, logger=print, timeout=60) -> Optional[str]:
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
    headers = {"Authorization": f"Bearer {token}"}
    with open(zip_path, "rb") as f:
        files = {"file": (zip_path.name, f, "application/zip")}
        r = requests.post(upload_url, headers=headers, files=files, timeout=180)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}

def test_comm(token_url: str, client_id: str, client_secret: str, logger=print) -> bool:
    tok = get_token(token_url, client_id, client_secret, logger=logger)
    return tok is not None
