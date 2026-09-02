from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. ID de la señal en vivo de TVN y del reproductor
        media_id = "57a498c4d7b86d600e5461cb"
        player_id = "57f40bb4dc5b9f3075c49cfe"
        
        # 2. URL de incrustación de Mediastream
        embed_url = f"https://mdstrm.com/live-stream/{media_id}?jsapi=true&autoplay=true&player={player_id}"
        
        req = urllib.request.Request(
            embed_url, 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.tvn.cl/",
                "Accept-Language": "es-ES,es;q=0.9"
            }
        )
        
        try:
            # Consultar la vista de incrustación de Mediastream
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # 3. Extraer el token de acceso mediante expresiones regulares
            # Busca patrones como access_token="xxxx" o access_token: "xxxx" o token dentro de URLs
            token_match = re.search(r'access_token[=:]\s*["\']?([a-zA-Z0-9_\-]+)["\']?', html)
            
            if token_match:
                token = token_match.group(1)
                m3u8_url = f"https://mdstrm.com/live-stream-playlist/{media_id}.m3u8?access_token={token}&player={player_id}"
            else:
                # Buscar directamente una URL .m3u8 completa si viene incrustada
                url_match = re.search(r'https://mdstrm\.com/live-stream-playlist/[^"\']+\.m3u8[^"\']+', html)
                m3u8_url = url_match.group(0) if url_match else None

            if m3u8_url:
                # Limpiar caracteres escapados de JavaScript si los hay (\/)
                m3u8_url = m3u8_url.replace('\\/', '/')
                
                # 4. Redirección HTTP 302 hacia la lista de reproducción HLS
                self.send_response(302)
                self.send_header('Location', m3u8_url)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"Error: No se encontro el token ni la URL m3u8 en el reproductor.")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Error al obtener transmision: {str(e)}".encode('utf-8'))