import glob
import json
import re
import ssl
import time
import unicodedata
import urllib.error
import urllib.request
from playwright.sync_api import sync_playwright

# Desactivar verificación SSL estricta
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}

ALIAS_CANALES = {
    'Los Simpsons': [],
    '31 Minutos': [],
    'La Red': ['La Red ✪ | CL'],
    'UCV': ['UCV | CL'],
    'UCV 2': ['UCV 2 | CL'],
    'TV+': ['TV+ ✪ | CL'],
    'TVN': ['TVN ✪ | CL'],
    'Canal 24 Horas': ['TVN 24 Horas ✪ | CL'],
    'NTV': ['NTV ✪ | CL'],
    'TV Chile': ['TV Chile ✪ | CL'],
    'TVN3': ['TVN3 ✪ | CL'],
    'Mega': ['Mega ✪ | CL'],
    'Meganoticias': ['Meganoticias ✪ | CL'],
    'Mega 2': ['Mega 2 (1080p)'],
    'Chilevisión': ['CHV ✪ | CL'],
    'CHV Noticias': ['CHV Noticias ✪ | CL'],
    'CHV Deportes': ['CHV Deportes ✪ | CL'],
    'Canal 13': ['Canal 13 ✪ | CL'],
    'T13 Noticias': ['T13 ✪ | CL'],
    '13 Cultura': ['13 Cultura | CL'],
    '13c': ['13 C'],
    '13 Cocina': ['13 Cocina | CL'],
    '13 Pop': ['13 Pop | CL'],
    '13 Teleseries': ['13 Teleseries | CL'],
    '13 Festival': ['13 Festival | CL'],
    '13 Realities': ['13 Realities | CL'],
    '13 Viajes': ['13 Viajes | CL'],
    '13 go': ['13 go ✪ | CL'],
    '13 Deportes': ['D13 | CL'],
    'FutGO': ['FutGO | CL'],
    'El canal feliz': [
        'El Canal Feliz ✪ | CL',
        'El Canal Feliz',
        'El Canal Feliz (720p)',
    ],
    'CNN Chile': ['CNN Chile ✪ | CL', 'CNN Chile'],
    'ESPN': ['ESPN', 'ESPN HD'],
    'ESPN 2': ['ESPN 2', 'ESPN 2 HD'],
    'ESPN 3': ['49 ESPN 3 HD'],
    'ESPN 4': ['ESPN 4 HD'],
    'TNT Sports Premium': [
        'TNT Sports Premium HD',
        'TNT Sports Premium SD',
    ],
    'AXN': ['AXN', '76 AXN HD'],
    'Warner TV': ['Warner TV HD', 'Warner Channel'],
    'Cinecanal': [
        'Cinecanal',
        'Cinecanal HD',
    ],
    'Star Channel': [
        'Star Channel',
        'Star Channel HD',
        'STAR CHANNEL',
    ],
    'FX': [
        'FX',
        'FX HD',
    ],
    'Studio Universal': [
        'Studio Universal',
        'Studio Universal HD',
    ],
    'HBO': ['HBO', 'HBO HD'],
    'HBO Family': ['HBO Family HD'],
    'HBO +': ['HBO +'],
    'HBO Xtreme': ['HBO Xtreme HD'],
    'HBO 2': ['HBO 2', 'HBO2 HD', 'Hbo 2'],
    'CINEMAX': ['71 Cinemax'],
    'TNT': ['TNT HD', 'TNT'],
    'SPACE': ['Space', 'Space HD'],
    'Sony Movies': ['Sony Movies', 'Sony Movies HD'],
    'Sony Channel': [
        'Sony',
        'Sony HD',
    ],
    'Sony Cine': ['Cine Sony (1080p)'],
    'Telemundo Internacional': [
        'Telemundo',
        'Telemundo HD',
        '34 Telemundo',
    ],
    'Telemundo Noticias': [],
    'Nat Geo': ['Nat Geo HD'],
    'A&E': ['A&E', 'A&E HD'],
    'AMC': ['AMC', '74 AMC HD'],
    'Discovery Channel': ['Discovery Channel', '44 Discovery Channel HD'],
    'History': [
        'History Channel',
        'History Channel HD',
    ],
    'History 2': ['History 2'],
    'Film & Arts': ['Film&Arts', 'Film & Arts (1080p)'],
    'Cartoon Network': ['Cartoon Network HD'],
    'Disney Channel': [
        'Disney Channel',
        'Disney Channel HD',
    ],
    'Nickelodeon': ['02 Nickelodeon HD'],
    'Nicktoons': ['Nickelodeon Toons (720p)'],
    'Bob Esponja': ['Bob Esponja Pantalones Cuadrados (720p)'],
    'Venus': ['Venus'],
    'PlayBoy': ['PLAY BOY', 'Playboy HD'],
    'Sextreme': ['SEX XTREME'],
    'Asian': ['Asian'],
    'Live Cams': ['Live Cams'],
    'MILF': ['MILF'],
    'Big Tits': ['Big Tits'],
    'Pornstar': ['Pornstar'],
    'Big Ass': ['Big Ass'],
    'Interracial': ['Interracial'],
    'Latina': ['Latina'],
    'Russian': ['Russian'],
    'Lesbian': ['Lesbian'],
    'Anal': ['Anal'],
    'Teen': ['Teen'],
}

M3U_CACHE = {}


def normalizar_texto(texto):
  if not texto:
    return ''
  texto = texto.lower()
  texto = unicodedata.normalize('NFD', texto)
  texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
  texto = re.sub(
      r'\b(hd|fhd|sd|uhd|4k|8k|raw|vip|hevc|h264|h265|1080p|720p)\b', '', texto
  )
  texto = re.sub(r'[^a-z0-9]', '', texto)
  return texto.strip()


def extraer_canales_de_lineas(lines, m3u_channels):
  current_name = None
  for line in lines:
    line = line.strip()
    if line.startswith('#EXTINF:'):
      if ',' in line:
        current_name = line.split(',')[-1].strip()
      else:
        current_name = None
    elif line.startswith(('http://', 'https://')) and current_name:
      norm_name = normalizar_texto(current_name)
      if norm_name:
        if norm_name not in m3u_channels:
          m3u_channels[norm_name] = []
        if line not in m3u_channels[norm_name]:
          m3u_channels[norm_name].append(line)
      current_name = None


def procesar_fuente_m3u(fuente):
  if fuente in M3U_CACHE:
    return M3U_CACHE[fuente]

  m3u_channels = {}
  if fuente.startswith(('http://', 'https://')):
    print(f'🌐 Descargando M3U desde URL: {fuente}')
    try:
      req = urllib.request.Request(fuente, headers=HEADERS)
      with urllib.request.urlopen(
          req, timeout=10, context=ssl_context
      ) as response:
        contenido = response.read().decode('utf-8', errors='ignore')
        extraer_canales_de_lineas(contenido.splitlines(), m3u_channels)
        print('  ✅ Lista web procesada correctamente.')
    except Exception as e:
      print(f'  ❌ Error descargando desde URL: {e}')
  else:
    archivos = glob.glob(fuente)
    for file_path in archivos:
      print(f'📁 Leyendo archivo M3U local: {file_path}')
      try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
          extraer_canales_de_lineas(f.readlines(), m3u_channels)
      except Exception as e:
        print(f'  ❌ Error leyendo archivo local {file_path}: {e}')

  M3U_CACHE[fuente] = m3u_channels
  return m3u_channels


def parse_m3u_sources(fuentes_m3u):
  m3u_combined = {}
  for fuente in fuentes_m3u:
    data = procesar_fuente_m3u(fuente)
    for name, urls in data.items():
      if name not in m3u_combined:
        m3u_combined[name] = []
      for u in urls:
        if u not in m3u_combined[name]:
          m3u_combined[name].append(u)
  return m3u_combined


def verificar_url(url, timeout=5):
  req = urllib.request.Request(url, headers=HEADERS)
  start_time = time.time()
  try:
    with urllib.request.urlopen(
        req, timeout=timeout, context=ssl_context
    ) as response:
      elapsed_time = round(time.time() - start_time, 3)
      status = response.getcode()
      if 200 <= status < 400:
        return True, elapsed_time
      else:
        return False, float('inf')
  except Exception:
    return False, float('inf')


def obtener_busquedas_canal(nombre_canal):
  busquedas = set()
  busquedas.add(normalizar_texto(nombre_canal))

  tiene_alias_explicito = False
  if nombre_canal in ALIAS_CANALES and ALIAS_CANALES[nombre_canal]:
    tiene_alias_explicito = True
    for alias in ALIAS_CANALES[nombre_canal]:
      norm_alias = normalizar_texto(alias)
      if norm_alias:
        busquedas.add(norm_alias)

  return list(busquedas), tiene_alias_explicito


def obtener_token_dinamico():
  """Abre la web objetivo con Playwright para extraer el token renderizado."""
  url_pagina = 'https://spinoff.link/listas-gomex/'
  print(f'🔎 Extrayendo TOKEN desde {url_pagina}...')
  try:
    with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto(url_pagina, wait_until='networkidle')
      content = page.content()
      browser.close()

      # Capturar token de 3 a 6 caracteres alfanuméricos
      match = re.search(
          r'tecnotv\.club/([a-zA-Z0-9]{3,6})/geomex\.m3u', content, re.IGNORECASE
      )
      if match:
        token = match.group(1)
        print(f'🔑 Token detectado con éxito: {token}')
        return token
  except Exception as e:
    print(f'❌ Error al extraer token con Playwright: {e}')

  print('⚠️ Usando token por defecto (e7nu).')
  return 'e7nu'


def update_json_streams(
    json_file_path,
    fuentes_m3u_generales,
    fuentes_por_canal,
    output_json_path,
    modo_acumular=True,
    verificar_conexion=True,
    timeout_seg=5,
):
  try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
      json_data = json.load(f)
  except Exception as e:
    print(f'Error leyendo el JSON base {json_file_path}: {e}')
    return

  canales = json_data.get('canales', [])
  canales_actualizados = 0
  urls_eliminadas = 0

  for canal in canales:
    nombre_original = canal.get('name', '')

    if nombre_original in fuentes_por_canal:
      fuentes_a_usar = fuentes_por_canal[nombre_original]
    else:
      fuentes_a_usar = fuentes_m3u_generales

    m3u_data = parse_m3u_sources(fuentes_a_usar)
    variantes_busqueda, tiene_alias = obtener_busquedas_canal(nombre_original)
    urls_encontradas = []

    for m3u_name, urls in m3u_data.items():
      for var in variantes_busqueda:
        if not var:
          continue
        if tiene_alias:
          if var == m3u_name:
            urls_encontradas.extend(urls)
            break
        else:
          if (
              var == m3u_name
              or (len(var) > 3 and var in m3u_name)
              or (len(m3u_name) > 3 and m3u_name in var)
          ):
            urls_encontradas.extend(urls)
            break

    urls_encontradas = list(dict.fromkeys(urls_encontradas))

    if urls_encontradas:
      if modo_acumular:
        urls_existentes = {s['url'] for s in canal.get('stream', [])}
        for url in urls_encontradas:
          if url not in urls_existentes:
            canal.setdefault('stream', []).append({'type': 'direct', 'url': url})
      else:
        streams_fijos = [
            st for st in canal.get('stream', []) if st.get('fixed') is True
        ]
        nuevos_streams = [
            {'type': 'direct', 'url': url} for url in urls_encontradas
        ]
        canal['stream'] = streams_fijos + nuevos_streams
      canales_actualizados += 1

    if 'stream' in canal and canal['stream']:
      streams_con_tiempo = []
      for st in canal['stream']:
        url = st.get('url')
        es_fijo = st.get('fixed', False)
        if url:
          if es_fijo:
            streams_con_tiempo.append((-1, st))
          elif verificar_conexion:
            es_valida, latencia = verificar_url(url, timeout=timeout_seg)
            if es_valida:
              streams_con_tiempo.append((latencia, st))
            else:
              urls_eliminadas += 1
          else:
            streams_con_tiempo.append((0, st))

      streams_con_tiempo.sort(key=lambda item: item[0])
      canal['stream'] = [item[1] for item in streams_con_tiempo]

    if canal.get('stream'):
      canal['active'] = True
    else:
      canal['active'] = False

  with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)

  print('Proceso finalizado correctamente.')


if __name__ == '__main__':
  # Ruta ajustada a tu repositorio
  JSON_ENTRADA = 'data/canales.json'
  JSON_SALIDA = 'data/canales.json'

  TOKEN = obtener_token_dinamico()

  FUENTES_M3U_GENERALES = [
      '*.m3u',
      'https://www.m3u.cl/lista/CL.m3u',
      'https://iptv-org.github.io/iptv/languages/spa.m3u',
      f'https://tecnotv.club/{TOKEN}/geomex.m3u',
      f'https://tecnotv.club/{TOKEN}/lista.m3u',
      f'https://tecnotv.club/{TOKEN}/lista1.m3u',
      f'https://tecnotv.club/{TOKEN}/lista2.m3u',
      f'https://tecnotv.club/{TOKEN}/lista3.m3u',
      f'https://tecnotv.club/{TOKEN}/lista4.m3u',
      f'https://tecnotv.club/{TOKEN}/android.m3u',
      f'https://tecnotv.club/{TOKEN}/android1.m3u',
      f'https://tecnotv.club/{TOKEN}/android2.m3u',
      f'https://tecnotv.club/{TOKEN}/android3.m3u',
      f'https://tecnotv.club/{TOKEN}/listahot.m3u',
  ]

  FUENTES_POR_CANAL = {
      'Los Simpsons': [],
      '31 Minutos': [],
      'La Red': ['https://www.m3u.cl/lista/CL.m3u'],
      'UCV': ['https://www.m3u.cl/lista/CL.m3u'],
      'UCV 2': ['https://www.m3u.cl/lista/CL.m3u'],
      'TV+': ['https://www.m3u.cl/lista/CL.m3u'],
      'TVN': ['https://www.m3u.cl/lista/CL.m3u'],
      'Canal 24 Horas': ['https://www.m3u.cl/lista/CL.m3u'],
      'NTV': ['https://www.m3u.cl/lista/CL.m3u'],
      'TV Chile': ['https://www.m3u.cl/lista/CL.m3u'],
      'TVN3': ['https://www.m3u.cl/lista/CL.m3u'],
      'Mega': ['https://www.m3u.cl/lista/CL.m3u'],
      'Meganoticias': ['https://www.m3u.cl/lista/CL.m3u'],
      'Mega 2': ['https://iptv-org.github.io/iptv/languages/spa.m3u'],
      'Chilevisión': ['https://www.m3u.cl/lista/CL.m3u'],
      'CHV Noticias': ['https://www.m3u.cl/lista/CL.m3u'],
      'CHV Deportes': ['https://www.m3u.cl/lista/CL.m3u'],
      'Canal 13': ['https://www.m3u.cl/lista/CL.m3u'],
      'T13 Noticias': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Cultura': ['https://www.m3u.cl/lista/CL.m3u'],
      '13c': [],
      '13 Cocina': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Pop': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Teleseries': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Festival': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Realities': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Viajes': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 go': ['https://www.m3u.cl/lista/CL.m3u'],
      '13 Deportes': ['https://www.m3u.cl/lista/CL.m3u'],
      'FutGO': ['https://www.m3u.cl/lista/CL.m3u'],
      'El canal feliz': [
          'https://www.m3u.cl/lista/CL.m3u',
          'https://iptv-org.github.io/iptv/languages/spa.m3u',
      ],
      'CNN Chile': [
          f'https://tecnotv.club/{TOKEN}/android1.m3u',
          'https://www.m3u.cl/lista/CL.m3u',
      ],
      'CNN Español': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'ESPN': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'ESPN 2': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'ESPN 3': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'ESPN 4': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'TNT Sports Premium': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'AXN': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Warner TV': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Cinecanal': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Star Channel': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'FX': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Studio Universal': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'HBO': [
          f'https://tecnotv.club/{TOKEN}/android1.m3u',
          f'https://tecnotv.club/{TOKEN}/lista.m3u',
          f'https://tecnotv.club/{TOKEN}/lista2.m3u',
      ],
      'HBO Family': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'HBO +': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'HBO Xtreme': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'HBO 2': [f'https://tecnotv.club/{TOKEN}/lista4.m3u'],
      'CINEMAX': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'TNT': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'SPACE': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Sony Movies': [
          f'https://tecnotv.club/{TOKEN}/android1.m3u',
          f'https://tecnotv.club/{TOKEN}/lista.m3u',
      ],
      'Sony Channel': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Sony Cine': ['https://iptv-org.github.io/iptv/languages/spa.m3u'],
      'Telemundo Internacional': [
          f'https://tecnotv.club/{TOKEN}/android1.m3u',
          f'https://tecnotv.club/{TOKEN}/lista.m3u',
      ],
      'Telemundo Noticias': [],
      'Nat Geo': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'A&E': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'AMC': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Discovery Channel': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'History': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'History 2': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Film & Arts': [
          f'https://tecnotv.club/{TOKEN}/android1.m3u',
          'https://iptv-org.github.io/iptv/languages/spa.m3u',
      ],
      'Cartoon Network': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Disney Channel': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Nickelodeon': [f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Nicktoons': ['https://iptv-org.github.io/iptv/languages/spa.m3u'],
      'Bob Esponja': ['https://www.m3u.cl/lista/CL.m3u'],
      'Venus': [f'https://tecnotv.club/{TOKEN}/geomex.m3u', f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'PlayBoy': [f'https://tecnotv.club/{TOKEN}/geomex.m3u', f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Sextreme': [f'https://tecnotv.club/{TOKEN}/geomex.m3u', f'https://tecnotv.club/{TOKEN}/android1.m3u'],
      'Asian': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Live Cams': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'MILF': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Big Tits': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Pornstar': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Big Ass': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Interracial': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Latina': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Russian': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Lesbian': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Anal': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
      'Teen': [f'https://tecnotv.club/{TOKEN}/listahot.m3u'],
  }

  update_json_streams(
      JSON_ENTRADA,
      FUENTES_M3U_GENERALES,
      FUENTES_POR_CANAL,
      JSON_SALIDA,
      modo_acumular=True,
      verificar_conexion=True,
      timeout_seg=5,
  )