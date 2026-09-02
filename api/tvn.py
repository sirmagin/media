from http.server import BaseHTTPRequestHandler
import urllib.request
import ssl
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        media_id = "57a498c4d7b86d600e5461cb"
        player_id = "57f40bb4dc5b9f3075c49cfe"
        
        # URL completa con parametros que espera la plataforma
        target_url = (
            f"https://mdstrm.com/live-stream/{media_id}"
            f"?jsapi=true&autoplay=true&controls=false&volume=100&player={player_id}"
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.tvn.cl/",
            "Origin": "https://www.tvn.cl",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
            "Connection": "keep-alive"
        }
        
        req = urllib.request.Request(target_url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, timeout=8, context=ctx) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            # Buscar el token de acceso en el HTML/JS devuelto
            token_match = re.search(r'access_token[=:]\s*["\']?([a-zA-Z0-9_\-]+)["\']?', html)
            
            if token_match:
                token = token_match.group(1)
                m3u8_url = f"https://mdstrm.com/live-stream-playlist/{media_id}.m3u8?access_token={token}&player={player_id}"
            else:
                # Buscar directamente el enlace m3u8 completo
                url_match = re.search(r'https://mdstrm\.com/live-stream-playlist/[^"\']+\.m3u8[^"\']+', html)
                m3u8_url = url_match.group(0).replace('\\/', '/') if url_match else None

            if m3u8_url:
                self.send_response(302)
                self.send_header('Location', m3u8_url)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"Error: Token no encontrado en la respuesta del reproductor.")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Error de conexion: {str(e)}".encode('utf-8'))