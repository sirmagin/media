from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        media_id = "57a498c4d7b86d600e5461cb"
        player_id = "57f40bb4dc5b9f3075c49cfe"
        target_url = f"https://mdstrm.com/live-stream/{media_id}?jsapi=true&autoplay=true&player={player_id}"
        
        # Usar AllOrigins para evadir el bloqueo HTTP 403 por IP de Vercel
        proxy_url = f"https://api.allorigins.win/get?url={urllib.parse.quote(target_url)}"
        
        try:
            req = urllib.request.Request(proxy_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                html = data.get("contents", "")
            
            token_match = re.search(r'access_token[=:]\s*["\']?([a-zA-Z0-9_\-]+)["\']?', html)
            
            if token_match:
                token = token_match.group(1)
                m3u8_url = f"https://mdstrm.com/live-stream-playlist/{media_id}.m3u8?access_token={token}&player={player_id}"
            else:
                url_match = re.search(r'https://mdstrm\.com/live-stream-playlist/[^"\']+\.m3u8[^"\']+', html)
                m3u8_url = url_match.group(0) if url_match else None

            if m3u8_url:
                self.send_response(302)
                self.send_header('Location', m3u8_url)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"Error: No se pudo extraer el token a traves del proxy.")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Error Proxy: {str(e)}".encode('utf-8'))