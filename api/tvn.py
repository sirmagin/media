import requests
import re
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. URL base del reproductor de Mediastream
        embed_url = "https://mdstrm.com/live-stream/57a498c4d7b86d600e5461cb?jsapi=true&autoplay=true"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://mdstrm.com/"
        }
        
        try:
            # 2. Consultar el reproductor
            res = requests.get(embed_url, headers=headers, timeout=5)
            
            # 3. Buscar la URL con el access_token renovado
            match = re.search(r'https://mdstrm\.com/live-stream-playlist/[^"\']+\.m3u8[^"\']+', res.text)
            
            if match:
                m3u8_url = match.group(0)
                # Redirigir al reproductor con HTTP 302
                self.send_response(302)
                self.send_header('Location', m3u8_url)
                self.end_headers()
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error: Token no encontrado")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())