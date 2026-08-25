# -*- coding: utf-8 -*-
"""
Turso Cloud SQLite Adapter (Pure Python HTTP Pipeline Client)
Provides a drop-in sqlite3-compatible interface for Turso LibSQL Cloud Database
with zero binary dependencies, working across all platforms and serverless functions.
"""
import os
import json
import base64
import requests

class TursoRow(dict):
    """Dictionary subclass that allows integer indexing like sqlite3.Row"""
    def __init__(self, cols, values):
        self._cols = cols
        self._values = values
        super().__init__(zip(cols, values))
    
    def __getitem__(self, item):
        if isinstance(item, int):
            return self._values[item]
        return super().__getitem__(item)
    
    def keys(self):
        return self._cols

class TursoCursor:
    def __init__(self, connection):
        self.connection = connection
        self._results = []
        self._pos = 0
        self.lastrowid = None
        self.rowcount = -1
        self.description = None

    def _convert_arg(self, val):
        if val is None:
            return {"type": "null"}
        elif isinstance(val, bool):
            return {"type": "integer", "value": "1" if val else "0"}
        elif isinstance(val, int):
            return {"type": "integer", "value": str(val)}
        elif isinstance(val, float):
            return {"type": "float", "value": float(val)}
        elif isinstance(val, bytes):
            return {"type": "blob", "base64": base64.b64encode(val).decode('utf-8')}
        else:
            return {"type": "text", "value": str(val)}

    def _parse_row_value(self, cell):
        t = cell.get("type")
        v = cell.get("value")
        if t == "null" or v is None:
            return None
        elif t == "integer":
            return int(v)
        elif t == "float":
            return float(v)
        elif t == "blob":
            b64 = cell.get("base64", "")
            return base64.b64decode(b64)
        else:
            return str(v)

    def execute(self, sql, params=None):
        sql = sql.strip()
        # Handle PRAGMAs that are not supported or needed remotely
        if sql.upper().startswith("PRAGMA FOREIGN_KEYS"):
            self._results = []
            self._pos = 0
            self.rowcount = 0
            return self

        args = []
        if params:
            if isinstance(params, (list, tuple)):
                args = [self._convert_arg(p) for p in params]
            elif isinstance(params, dict):
                # Named parameters
                for k, v in params.items():
                    args.append(self._convert_arg(v))

        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": args
                    }
                },
                {"type": "close"}
            ]
        }

        resp = self.connection._send_pipeline(payload)
        self._results = []
        self._pos = 0

        # Check response
        results = resp.get("results", [])
        if not results:
            return self

        first = results[0]
        if first.get("type") == "error":
            err_msg = first.get("error", {}).get("message", "Unknown Turso Error")
            raise Exception(f"Turso SQL Error: {err_msg}")

        exec_res = first.get("response", {}).get("result", {})
        cols = [c["name"] for c in exec_res.get("cols", [])]
        raw_rows = exec_res.get("rows", [])
        
        self.description = [(c, None, None, None, None, None, None) for c in cols] if cols else None
        self.rowcount = exec_res.get("affected_row_count", len(raw_rows))
        
        last_id = exec_res.get("last_insert_rowid")
        self.lastrowid = int(last_id) if last_id is not None else None

        for row in raw_rows:
            parsed_vals = [self._parse_row_value(c) for c in row]
            self._results.append(TursoRow(cols, parsed_vals))

        return self

    def executemany(self, sql, seq_of_params):
        for params in seq_of_params:
            self.execute(sql, params)
        return self

    def fetchone(self):
        if self._pos < len(self._results):
            row = self._results[self._pos]
            self._pos += 1
            return row
        return None

    def fetchall(self):
        remaining = self._results[self._pos:]
        self._pos = len(self._results)
        return remaining

    def close(self):
        self._results = []

class TursoConnection:
    def __init__(self, url, auth_token):
        # Format URL
        url = url.strip()
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        if not url.endswith("/v2/pipeline"):
            url = url.rstrip("/") + "/v2/pipeline"

        self.endpoint = url
        self.auth_token = auth_token.strip()
        self.row_factory = TursoRow

    def _send_pipeline(self, payload):
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        r = requests.post(self.endpoint, json=payload, headers=headers, timeout=15)
        if r.status_code != 200:
            raise Exception(f"Turso HTTP {r.status_code}: {r.text}")
        return r.json()

    def cursor(self):
        return TursoCursor(self)

    def execute(self, sql, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def executemany(self, sql, seq_of_params):
        cur = self.cursor()
        return cur.executemany(sql, seq_of_params)

    def commit(self):
        pass  # Auto-committed over HTTP pipeline

    def rollback(self):
        pass

    def close(self):
        pass

def connect_turso(url=None, token=None):
    url = url or os.environ.get("TURSO_DATABASE_URL") or os.environ.get("DATABASE_URL")
    token = token or os.environ.get("TURSO_AUTH_TOKEN") or ""
    if not url:
        raise ValueError("Missing TURSO_DATABASE_URL")
    return TursoConnection(url, token)
