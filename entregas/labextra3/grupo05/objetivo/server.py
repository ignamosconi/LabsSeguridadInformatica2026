#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Lab Extra 3 — copia PARCHADA del objetivo. Grupo 05, CyberLab UTN FRVM.
# Original (vulnerable) en labs/labextra3-hardening/objetivo/server.py.
"""
objetivo/server.py — PhantomCorp endurecida (Lab Extra 3).

Las cinco defensas D1–D5 que exploramos en los labs 05–07, cerradas aquí con
fixes ESTRUCTURALES (no cosméticos). Cada bloque marca el "antes" y el porqué:

  D1  banner Server genérico, sin producto ni versión          (era info leak)
  D2  /api/status no existe en producción                      (era debug en prod)
  D3  /backup exige autorización (401) y robots no la lista     (era 200 sin auth)
  D4  /login usa consulta parametrizada (?)                     (era SQLi por f-string)
  D5  /descargar confina el acceso al directorio público        (era path traversal)

La app sigue funcionando: `/` responde, el login legítimo
(admin / sup3r-s3cr3t0) entra, y /descargar?archivo=manual.txt descarga.
Solo stdlib.
"""
import base64
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

DB = "/tmp/phantom_hardening.db"
DESCARGAS = "/tmp/phantom_descargas"    # raíz "pública" de /descargar

# D4: credenciales legítimas, usadas también para autorizar /backup (D3).
USUARIO_OK = "admin"
PASSWORD_OK = "sup3r-s3cr3t0"


def init_db():
    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE usuarios (user TEXT, password TEXT)")
    db.execute("INSERT INTO usuarios VALUES (?, ?)", (USUARIO_OK, PASSWORD_OK))
    db.commit()
    db.close()
    os.makedirs(DESCARGAS, exist_ok=True)
    with open(os.path.join(DESCARGAS, "manual.txt"), "w") as fh:
        fh.write("Manual de la intranet PhantomCorp.\n")


class Handler(BaseHTTPRequestHandler):
    # D1 — ANTES: server_version = "PhantomServer/2.4.1-debug" cantaba producto,
    # versión y hasta el modo debug. AHORA: banner genérico, sin nada que
    # identifique el software ni su versión. (No es "la" defensa, es higiene:
    # ver P3 sobre seguridad por oscuridad.)
    server_version = "PhantomCorp"
    sys_version = ""

    def do_GET(self):
        path, _, qs = self.path.partition("?")
        params = parse_qs(qs)

        if path == "/":
            self._html(200, "<h1>PhantomCorp</h1><p>Portal de empleados.</p>")
        elif path == "/robots.txt":
            # D3 — ANTES: el robots listaba /backup y /api/status, sirviéndole
            # el mapa al atacante. AHORA: robots neutro. (robots NO es un control
            # de acceso; proteger la ruta es lo que cuenta — ver P2.)
            self._txt(200, "User-agent: *\nDisallow:\n")
        elif path == "/backup":
            # D3 — ANTES: respondía 200 sin autenticación. AHORA: exige
            # autorización; sin credencial válida -> 401. El fix real es
            # proteger el recurso, no esconderlo del robots.
            if not self._autorizado():
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="backup"')
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"401 - no autorizado")
            else:
                self._txt(200, "dump_pre_migracion: usuarios=1 OK")
        # D2 — ANTES: /api/status exponía debug:true, env, ruta de la DB y PID
        # en producción. AHORA: el endpoint no existe; cae en el 404 de abajo.
        elif path == "/login":
            # D4 — ANTES: la query se armaba por interpolación de strings
            # ("... WHERE user = '" + user + "' ..."), vulnerable a
            # ' OR 1=1 -- y admin'--. AHORA: consulta PARAMETRIZADA: los valores
            # viajan separados del SQL, el motor nunca los interpreta como código.
            user = params.get("user", [""])[0]
            pwd = params.get("pass", [""])[0]
            db = sqlite3.connect(DB)
            cur = db.execute(
                "SELECT user FROM usuarios WHERE user = ? AND password = ?",
                (user, pwd))
            fila = cur.fetchone()
            db.close()
            if fila:
                # escapamos el reflejo del nombre para no cambiar un SQLi por un XSS.
                self._html(200, "<h1>Bienvenido, " + self._escapar(fila[0]) + "</h1>")
            else:
                self._html(401, "<h1>Credenciales inválidas</h1>")
        elif path == "/descargar":
            # D5 — ANTES: ruta = DESCARGAS + "/" + nombre y se abría cualquier
            # cosa (../../etc/passwd, /etc/passwd, %2e%2e...). AHORA: se resuelve
            # el path real y se EXIGE que quede dentro de DESCARGAS. Como
            # canonicalizamos con realpath, cae cualquier encoding/variante
            # (.. , %2e%2e , ....// , rutas absolutas): todas terminan fuera
            # de la base y se rechazan.
            nombre = params.get("archivo", [""])[0]
            base = os.path.realpath(DESCARGAS)
            ruta = os.path.realpath(os.path.join(base, nombre))
            if os.path.commonpath([base, ruta]) != base:
                self._txt(403, "prohibido")
                return
            try:
                with open(ruta, "rb") as fh:
                    self._txt(200, fh.read(8192).decode("utf-8", "ignore"))
            except Exception:
                self._txt(404, "no encontrado")
        else:
            self._txt(404, "404 - no existe")

    # --- autorización (D3) ---
    def _autorizado(self):
        cab = self.headers.get("Authorization", "")
        if not cab.startswith("Basic "):
            return False
        try:
            cred = base64.b64decode(cab[6:]).decode("utf-8", "ignore")
            user, _, pwd = cred.partition(":")
        except Exception:
            return False
        return user == USUARIO_OK and pwd == PASSWORD_OK

    # --- helpers de respuesta ---
    def _escapar(self, s):
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    def _html(self, code, body):
        self._send(code, body.encode(), "text/html; charset=utf-8")

    def _txt(self, code, body):
        self._send(code, body.encode(), "text/plain; charset=utf-8")

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    init_db()
    puerto = int(os.environ.get("PORT", "8080"))
    print(f"PhantomCorp (endurecida) en 0.0.0.0:{puerto}")
    ThreadingHTTPServer(("0.0.0.0", puerto), Handler).serve_forever()
