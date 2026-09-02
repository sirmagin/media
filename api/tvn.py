from http.server import BaseHTTPRequestHandler
import urllib.request
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ID de la transmisión en vivo de TVN
        media_id = "57a498c4d7b86d600e5461cb"
        player_id = "57f40bb4dc5b9f3075c49cfe"
        
        # Endpoint directo de la API interna de Mediastream
        api_url = f"https://mdstrm.com/api/client/live-stream/{media_id}?player={player_id}"
        
        req = urllib.request.Request(
            api_url, 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://mdstrm.com/"
            }
        )
        
        try:
            # 1. Consultar la API JSON de Mediastream
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 2. Obtener el access_token o la lista HLS desde la respuesta JSON
            access_token = data.get("access_token")
            
            # Construir la URL del .m3u8 si tenemos el token
            if access_token:
                m3u8_url = f"https://mdstrm.com/live-stream-playlist/{media_id}.m3u8?access_token={access_token}&player={player_id}&autoplay=true"
            else:
                # Si la API entrega directamente la URL HLS en las fuentes (src)
                src_list = data.get("src", {})
                m3u8_url = src_list.get("hls") or src_list.get("hls_direct")

            if m3u8_url:
                # 3. Redirección HTTP 302 hacia el .m3u8
                self.send_response(302)
                self.send_header('Location', m3u8_url)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"Error: La API de Mediastream no devolvio un token valido.")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Error al consultar API: {str(e)}".encode('utf-8'))