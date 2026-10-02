"""Exporta o arquivo Prometheus no serviço já existente do Compose."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import override


class ExportadorMetricas(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            corpo = b"ok"
        elif self.path == "/metrics":
            caminhos = [os.environ["METRICAS_TREINO_ARQUIVO"]]
            if adicional := os.environ.get("METRICAS_SERVING_ARQUIVO"):
                caminhos.append(adicional)
            corpo = b"\n".join(
                Path(caminho).read_bytes() for caminho in caminhos if Path(caminho).is_file()
            )
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    @override
    def log_message(self, format: str, *args: object) -> None:
        # Caminhos arbitrários de clientes não entram nos logs.
        return


if __name__ == "__main__":
    HTTPServer(
        (os.environ["METRICAS_HTTP_HOST"], int(os.environ["METRICAS_HTTP_PORT"])),
        ExportadorMetricas,
    ).serve_forever()
