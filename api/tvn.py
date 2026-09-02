from http.server import BaseHTTPRequestHandler
import requests
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        embed_url = "https://mdstrm.com/live-stream/57a498c4d7b86d600e5461cb?jsapi=true&autoplay=true"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://mdstrm.com/"
        }
        
        try:
            res = requests.get(embed_url, headers=headers, timeout=10)
            match = re.search(r'https://mdstrm\.com/live-stream-playlist/[^"\']+\.m3u8[^"\']+', res.text)
            
            if match:
                m3u8_url = match.group(0)
                # Enviar redirección HTTP 302 al reproductor
                self.send_response(302)
                self.send_header('Location', m3u8_url)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            else:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("Error: No se pudo extraer la lista m3u8 de Mediastream.".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Error de conexión: {str(e)}".encode('utf-8'))