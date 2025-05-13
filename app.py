import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import re
import requests
import zipfile
from io import BytesIO
import random
import matplotlib.pyplot as plt
import base64

# Configuración de la página - DEBE SER LO PRIMERO DESPUÉS DE IMPORTAR STREAMLIT
st.set_page_config(
    page_title="Consulta RENSPA - SENASA",
    page_icon="🌱",
    layout="wide"
)

# Intentar importar folium y streamlit_folium
try:
    import folium
    from folium.plugins import MeasureControl, MiniMap, MarkerCluster
    from streamlit_folium import folium_static
    folium_disponible = True
except ImportError:
    folium_disponible = False
    st.warning("Para visualizar mapas, instale folium y streamlit-folium")

# Configuraciones globales
API_BASE_URL = "https://aps.senasa.gob.ar/restapiprod/servicios/renspa"
TIEMPO_ESPERA = 0.5  # Pausa entre peticiones para no sobrecargar la API

# Estado de la aplicación
if 'poligonos_gee' not in st.session_state:
    st.session_state.poligonos_gee = []
if 'df_renspa' not in st.session_state:
    st.session_state.df_renspa = pd.DataFrame()
if 'cuit_actual' not in st.session_state:
    st.session_state.cuit_actual = ""
if 'analisis_cultivos' not in st.session_state:
    st.session_state.analisis_cultivos = False
if 'cultivos_por_poligono' not in st.session_state:
    st.session_state.cultivos_por_poligono = {}
if 'campana_seleccionada' not in st.session_state:
    st.session_state.campana_seleccionada = "Campaña 2020-2021"

# Función para normalizar CUIT
def normalizar_cuit(cuit):
    """Normaliza un CUIT a formato XX-XXXXXXXX-X"""
    cuit_limpio = cuit.replace("-", "")
    if len(cuit_limpio) != 11:
        raise ValueError(f"CUIT inválido: {cuit}. Debe tener 11 dígitos.")
    return f"{cuit_limpio[:2]}-{cuit_limpio[2:10]}-{cuit_limpio[10]}"

# Función para obtener RENSPA por CUIT
def obtener_renspa_por_cuit(cuit):
    """Obtiene todos los RENSPA asociados a un CUIT, manejando la paginación"""
    try:
        url_base = f"{API_BASE_URL}/consultaPorCuit"
        todos_renspa = []
        offset = 0
        limit = 10  # La API usa un límite de 10 por página
        has_more = True
        
        while has_more:
            url = f"{url_base}?cuit={cuit}&offset={offset}"
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                resultado = response.json()
                
                if 'items' in resultado and resultado['items']:
                    todos_renspa.extend(resultado['items'])
                    has_more = resultado.get('hasMore', False)
                    offset += limit
                else:
                    has_more = False
            except Exception as e:
                st.error(f"Error consultando la API: {str(e)}")
                has_more = False
                
            time.sleep(TIEMPO_ESPERA)
        return todos_renspa
    except Exception as e:
        st.error(f"Error al obtener RENSPA: {str(e)}")
        return []

# Función para normalizar RENSPA
def normalizar_renspa(renspa):
    """Normaliza un RENSPA al formato ##.###.#.#####/##"""
    renspa_limpio = renspa.strip()
    
    if re.match(r'^\d{2}\.\d{3}\.\d\.\d{5}/\d{2}$', renspa_limpio):
        return renspa_limpio
    
    if re.match(r'^\d{13}$', renspa_limpio):
        return f"{renspa_limpio[0:2]}.{renspa_limpio[2:5]}.{renspa_limpio[5:6]}.{renspa_limpio[6:11]}/{renspa_limpio[11:13]}"
    
    raise ValueError(f"Formato de RENSPA inválido: {renspa}")

# Función para consultar detalles de un RENSPA
def consultar_renspa_detalle(renspa):
    """Consulta los detalles de un RENSPA específico para obtener el polígono"""
    try:
        url = f"{API_BASE_URL}/consultaPorNumero?numero={renspa}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        st.error(f"Error consultando {renspa}: {e}")
        return None

# Función para extraer coordenadas de un polígono
def extraer_coordenadas(poligono_str):
    """Extrae coordenadas de un string de polígono en el formato de SENASA"""
    if not poligono_str or not isinstance(poligono_str, str):
        return None
    
    coord_pattern = r'\(([-\d\.]+),([-\d\.]+)\)'
    coord_pairs = re.findall(coord_pattern, poligono_str)
    
    if not coord_pairs:
        return None
    
    coords_geojson = []
    for lat_str, lon_str in coord_pairs:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            coords_geojson.append([lon, lat])  # GeoJSON usa [lon, lat]
        except ValueError:
            continue
    
    if len(coords_geojson) >= 3:
        if coords_geojson[0] != coords_geojson[-1]:
            coords_geojson.append(coords_geojson[0])  # Cerrar el polígono
        return coords_geojson
    
    return None

# Función para simular la consulta a Google Earth Engine
def consultar_gee_cultivos(poligonos, campana):
    """
    Simula una consulta a Google Earth Engine para obtener cultivos.
    En una implementación real, esta función enviaría los polígonos a GEE 
    y recibiría los resultados del análisis de cultivos.
    
    Args:
        poligonos: Lista de diccionarios con los polígonos
        campana: Cadena con la campaña seleccionada (ej: "Campaña 2020-2021")
        
    Returns:
        Diccionario con clasificación de cultivos por polígono
    """
    # Simulamos una respuesta de GEE
    cultivos_por_poligono = {}
    
    # Extraer año de la campaña
    year_match = re.search(r'(\d{4})-(\d{4})', campana)
    year1, year2 = 2020, 2021
    if year_match:
        year1, year2 = int(year_match.group(1)), int(year_match.group(2))
    
    # Lista de cultivos posibles según la campaña
    cultivos_base = ['Maíz', 'Soja 1ra', 'CI-Soja 2da', 'CI-Maíz 2da', 'No agrícola']
    
    # Añadir cultivos adicionales según la campaña
    if year1 >= 2021:
        cultivos_base.extend(['Girasol', 'Arroz'])
    if year1 >= 2022:
        cultivos_base.extend(['Sorgo GR', 'Algodón'])
    
    # Configuración por campaña
    porcentaje_agricola = {
        "Campaña 2019-2020": 0.22,  # 22% agrícola, 78% no agrícola
        "Campaña 2020-2021": 0.35,  # 35% agrícola, 65% no agrícola
        "Campaña 2021-2022": 0.45,  # 45% agrícola, 55% no agrícola
        "Campaña 2022-2023": 0.38,  # 38% agrícola, 62% no agrícola
        "Campaña 2023-2024": 0.41,  # 41% agrícola, 59% no agrícola
    }
    
    # Para cada polígono, generar una clasificación simulada
    for pol in poligonos:
        renspa = pol['renspa']
        superficie = pol.get('superficie', 100)
        cultivos_por_poligono[renspa] = []
        
        # Si no hay datos para la campaña, usar el promedio
        porc_agricola = porcentaje_agricola.get(campana, 0.35)
        
        # Determinar la superficie agrícola total
        superficie_agricola = superficie * porc_agricola
        superficie_no_agricola = superficie - superficie_agricola
        
        # Añadir "No agrícola"
        cultivos_por_poligono[renspa].append({
            'cultivo': 'No agrícola',
            'area': superficie_no_agricola,
            'porcentaje': round((superficie_no_agricola / superficie) * 100, 1)
        })
        
        # Distribuir el área agrícola entre los cultivos
        cultivos_agricolas = [c for c in cultivos_base if c != 'No agrícola']
        num_cultivos = min(3, len(cultivos_agricolas))  # Máximo 3 cultivos por polígono
        
        # Seleccionar cultivos para este polígono (seed con RENSPA para consistencia)
        random.seed(hash(renspa) % 10000)
        cultivos_seleccionados = random.sample(cultivos_agricolas, num_cultivos)
        
        # Distribuir superficie entre los cultivos seleccionados
        # Mayor superficie para el primer cultivo, menor para los siguientes
        pesos = [0.6, 0.3, 0.1][:num_cultivos]
        pesos = [p / sum(pesos) for p in pesos]
        
        for i, cultivo in enumerate(cultivos_seleccionados):
            area = superficie_agricola * pesos[i]
            porcentaje = round((area / superficie) * 100, 1)
            
            cultivos_por_poligono[renspa].append({
                'cultivo': cultivo,
                'area': area,
                'porcentaje': porcentaje
            })
    
    # Simular tiempo de procesamiento en GEE (2-3 segundos)
    time.sleep(2)
    
    return cultivos_por_poligono

# Función para generar un mapa con visualización de cultivos
def crear_mapa_cultivos(poligonos, cultivos_por_poligono, campana):
    """
    Crea un mapa folium con visualización de cultivos por polígono
    
    Args:
        poligonos: Lista de diccionarios con los datos de polígonos
        cultivos_por_poligono: Diccionario con la clasificación de cultivos por polígono
        campana: Campaña seleccionada
        
    Returns:
        Objeto mapa de folium
    """
    if not folium_disponible:
        st.warning("Para visualizar mapas, instale folium y streamlit-folium")
        return None
    
    if not poligonos:
        return None
    
    # Determinar centro del mapa
    all_lats = []
    all_lons = []
    for pol in poligonos:
        for coord in pol['coords']:
            all_lons.append(coord[0])
            all_lats.append(coord[1])
    
    if all_lats and all_lons:
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
    else:
        # Centro predeterminado (Buenos Aires)
        center_lat = -34.603722
        center_lon = -58.381592
    
    # Crear mapa base
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Agregar capas base con atribución
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                    name='Google Hybrid', 
                    attr='Google').add_to(m)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                    name='Google Satellite', 
                    attr='Google').add_to(m)
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    
    # Añadir herramienta de medición
    MeasureControl(position='topright', 
                  primary_length_unit='kilometers', 
                  secondary_length_unit='miles', 
                  primary_area_unit='hectares').add_to(m)
    
    # Añadir mini mapa para ubicación
    MiniMap().add_to(m)
    
    # Diccionario de colores por cultivo (similar a la imagen de GEE)
    colores_cultivo = {
        'Maíz': '#0042ff',         # Azul
        'Soja 1ra': '#339820',     # Verde
        'CI-Soja 2da': '#90ee90',  # Verde claro
        'CI-Maíz 2da': '#87CEEB',  # Azul claro
        'Arroz': '#1d1e33',        # Azul oscuro
        'No agrícola': '#646b63',  # Gris
        'Girasol': '#FFFF00',      # Amarillo
        'Sorgo GR': '#FF0000',     # Rojo
        'Algodón': '#b7b9bd',      # Gris claro
        'Default': '#FF0000'       # Rojo (por defecto)
    }
    
    # Crear grupos de capas para organizar la visualización
    fg_poligonos = folium.FeatureGroup(name="Polígonos RENSPA").add_to(m)
    fg_cultivos = {}
    
    # Crear un grupo para cada tipo de cultivo encontrado
    cultivos_unicos = set()
    for renspa, cultivos in cultivos_por_poligono.items():
        for cultivo_info in cultivos:
            cultivos_unicos.add(cultivo_info['cultivo'])
    
    for cultivo in cultivos_unicos:
        fg_cultivos[cultivo] = folium.FeatureGroup(name=f"Cultivo: {cultivo}").add_to(m)
    
    # Añadir cada polígono al mapa con su clasificación de cultivos
    for pol in poligonos:
        renspa = pol['renspa']
        
        # Información básica del polígono para popup
        popup_html = f"""
        <div style="width:250px;">
            <h4>RENSPA: {renspa}</h4>
            <p><b>Titular:</b> {pol.get('titular', 'No disponible')}</p>
            <p><b>Localidad:</b> {pol.get('localidad', 'No disponible')}</p>
            <p><b>Superficie:</b> {pol.get('superficie', 0)} ha</p>
        """
        
        # Agregar información de cultivos al popup
        if renspa in cultivos_por_poligono:
            popup_html += f"<h4>Clasificación ({campana.replace('Campaña ', '')}):</h4><ul>"
            
            for cultivo_info in cultivos_por_poligono[renspa]:
                cultivo = cultivo_info['cultivo']
                porcentaje = cultivo_info['porcentaje']
                area = cultivo_info['area']
                
                # Obtener color del cultivo
                color = colores_cultivo.get(cultivo, colores_cultivo['Default'])
                
                popup_html += f"""
                <li style="display:flex;align-items:center;margin-bottom:5px;">
                    <div style="width:15px;height:15px;background-color:{color};margin-right:5px;"></div>
                    {cultivo}: {area:.1f} ha ({porcentaje}%)
                </li>
                """
            
            popup_html += "</ul>"
        
        popup_html += "</div>"
        
        # Añadir borde del polígono (área total)
        folium.Polygon(
            locations=[[coord[1], coord[0]] for coord in pol['coords']],  # Invertir coordenadas para folium
            color='red',
            weight=2,
            fill=False,
            tooltip=f"RENSPA: {renspa}",
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(fg_poligonos)
        
        # Si hay datos de cultivos, visualizar subdivisiones de cultivos
        if renspa in cultivos_por_poligono:
            # Obtener el centro aproximado del polígono
            coords = [[coord[1], coord[0]] for coord in pol['coords']]  # Invertir coordenadas para folium
            center_x = sum(c[0] for c in coords) / len(coords)
            center_y = sum(c[1] for c in coords) / len(coords)
            
            # Para cada tipo de cultivo en este polígono
            porcentaje_acumulado = 0
            for cultivo_info in cultivos_por_poligono[renspa]:
                cultivo = cultivo_info['cultivo']
                porcentaje = cultivo_info['porcentaje']
                
                # Calcular el tamaño relativo basado en el porcentaje (desde el centro)
                porcentaje_escala = 1 - (porcentaje_acumulado / 100)
                porcentaje_siguiente = 1 - ((porcentaje_acumulado + porcentaje) / 100)
                
                # Crear polígono desde el centro, escalado según el porcentaje
                coords_cultivo_exterior = []
                for c in coords:
                    # Acercar el punto hacia el centro según el porcentaje acumulado
                    x = center_x + porcentaje_escala * (c[0] - center_x)
                    y = center_y + porcentaje_escala * (c[1] - center_y)
                    coords_cultivo_exterior.append([x, y])
                
                coords_cultivo_interior = []
                for c in coords:
                    # Acercar el punto más hacia el centro para el siguiente cultivo
                    x = center_x + porcentaje_siguiente * (c[0] - center_x)
                    y = center_y + porcentaje_siguiente * (c[1] - center_y)
                    coords_cultivo_interior.append([x, y])
                
                # Obtener color del cultivo
                color = colores_cultivo.get(cultivo, colores_cultivo['Default'])
                
                # Añadir área del cultivo al mapa
                folium.Polygon(
                    locations=coords_cultivo_exterior,
                    color=color,
                    weight=1,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    tooltip=f"{cultivo}: {cultivo_info['area']:.1f} ha ({porcentaje}%)"
                ).add_to(fg_cultivos.get(cultivo, fg_poligonos))
                
                # Actualizar el porcentaje acumulado
                porcentaje_acumulado += porcentaje
    
    # Añadir control de capas
    folium.LayerControl(position='topright').add_to(m)
    
    return m

# Función para generar tabla resumen de cultivos
def generar_resumen_cultivos(poligonos, cultivos_por_poligono):
    """
    Genera un resumen de cultivos para todos los polígonos
    
    Args:
        poligonos: Lista de diccionarios con los datos de polígonos
        cultivos_por_poligono: Diccionario con la clasificación de cultivos por polígono
        
    Returns:
        DataFrame con el resumen de cultivos
    """
    if not poligonos or not cultivos_por_poligono:
        return pd.DataFrame()
    
    # Calcular área total
    superficie_total = sum(p.get('superficie', 0) for p in poligonos)
    
    # Agregar cultivos de todos los polígonos
    cultivos_totales = {}
    
    for renspa, cultivos in cultivos_por_poligono.items():
        for cultivo_info in cultivos:
            cultivo = cultivo_info['cultivo']
            area = cultivo_info['area']
            
            if cultivo not in cultivos_totales:
                cultivos_totales[cultivo] = 0
            
            cultivos_totales[cultivo] += area
    
    # Crear DataFrame
    df_resumen = pd.DataFrame({
        'Cultivo': list(cultivos_totales.keys()),
        'Área (ha)': list(cultivos_totales.values())
    })
    
    # Calcular porcentajes
    df_resumen['Porcentaje (%)'] = (df_resumen['Área (ha)'] / superficie_total * 100).round(1)
    
    # Ordenar por área (descendente)
    df_resumen = df_resumen.sort_values('Área (ha)', ascending=False)
    
    # Redondear áreas
    df_resumen['Área (ha)'] = df_resumen['Área (ha)'].round(1)
    
    return df_resumen

# Función para crear la leyenda estilo GEE
def crear_leyenda_gee_cultivos(df_resumen, superficie_total, campana):
    """
    Crea HTML para una leyenda estilo GEE con cultivos
    
    Args:
        df_resumen: DataFrame con el resumen de cultivos
        superficie_total: Superficie total en hectáreas
        campana: Campaña seleccionada
        
    Returns:
        HTML de la leyenda
    """
    if df_resumen.empty:
        return ""
    
    # Diccionario de colores por cultivo
    colores_cultivo = {
        'Maíz': '#0042ff',         # Azul
        'Soja 1ra': '#339820',     # Verde
        'CI-Soja 2da': '#90ee90',  # Verde claro
        'CI-Maíz 2da': '#87CEEB',  # Azul claro
        'Arroz': '#1d1e33',        # Azul oscuro
        'No agrícola': '#646b63',  # Gris
        'Girasol': '#FFFF00',      # Amarillo
        'Sorgo GR': '#FF0000',     # Rojo
        'Algodón': '#b7b9bd',      # Gris claro
        'Default': '#FF0000'       # Rojo (por defecto)
    }
    
    # Extraer años de la campaña
    campana_nombre = campana.replace("Campaña ", "")
    
    # Inicio de la leyenda
    leyenda_html = f"""
    <div style="
        position: absolute;
        bottom: 20px;
        right: 10px;
        width: 280px;
        background-color: white;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
        font-size: 14px;
        z-index: 1000;
    ">
        <h4 style="margin-top: 0; margin-bottom: 10px; text-align: center; font-size: 16px;">
            {campana_nombre}
        </h4>
    """
    
    # Agregar cada cultivo
    for _, row in df_resumen.iterrows():
        cultivo = row['Cultivo']
        area = row['Área (ha)']
        porcentaje = row['Porcentaje (%)']
        
        # Obtener color del cultivo
        color = colores_cultivo.get(cultivo, colores_cultivo['Default'])
        
        leyenda_html += f"""
        <div style="display: flex; margin-bottom: 8px; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: {color}; margin-right: 8px;"></div>
            <div style="flex-grow: 1;">{cultivo}</div>
            <div style="font-weight: bold;">{int(area)} Ha ({int(porcentaje)}%)</div>
        </div>
        """
    
    # Agregar línea divisoria y total
    leyenda_html += f"""
        <div style="border-top: 1px solid #ccc; margin-top: 8px; padding-top: 8px;"></div>
        
        <div style="display: flex; align-items: center; font-weight: bold;">
            <div style="flex-grow: 1;">Área Total</div>
            <div>{int(superficie_total)} Ha</div>
        </div>
    </div>
    """
    
    return leyenda_html

# Función para procesar un CUIT
def procesar_cuit(cuit, solo_activos=True):
    """
    Procesa un CUIT para obtener todos sus RENSPA con polígonos
    
    Args:
        cuit: CUIT a procesar
        solo_activos: Si solo se deben procesar RENSPA activos
        
    Returns:
        df_renspa: DataFrame con todos los RENSPA
        poligonos_gee: Lista de polígonos extraídos
    """
    # Normalizar CUIT
    cuit_normalizado = normalizar_cuit(cuit)
    
    # Mostrar un indicador de procesamiento
    with st.status('Consultando RENSPA desde SENASA...', expanded=True) as status:
        # Crear barras de progreso
        progress_bar = st.progress(0)
        
        # Paso 1: Obtener todos los RENSPA para el CUIT
        status.update(label="Obteniendo listado de RENSPA...", state="running")
        progress_bar.progress(20)
        
        todos_renspa = obtener_renspa_por_cuit(cuit_normalizado)
        
        if not todos_renspa:
            status.update(label=f"No se encontraron RENSPA para el CUIT {cuit_normalizado}", state="error")
            return pd.DataFrame(), []
        
        # Crear DataFrame para mejor visualización y manipulación
        df_renspa = pd.DataFrame(todos_renspa)
        
        # Contar RENSPA activos e inactivos
        activos = df_renspa[df_renspa['fecha_baja'].isnull()].shape[0]
        inactivos = df_renspa[~df_renspa['fecha_baja'].isnull()].shape[0]
        
        status.update(label=f"Se encontraron {len(todos_renspa)} RENSPA ({activos} activos, {inactivos} inactivos)", state="running")
        
        # Filtrar según la opción seleccionada
        if solo_activos:
            renspa_a_procesar = df_renspa[df_renspa['fecha_baja'].isnull()].to_dict('records')
            status.write(f"Procesando {len(renspa_a_procesar)} RENSPA activos")
        else:
            renspa_a_procesar = todos_renspa
            status.write(f"Procesando todos los {len(renspa_a_procesar)} RENSPA")
        
        # Paso 2: Procesar los RENSPA para obtener los polígonos
        status.update(label="Obteniendo información de polígonos...", state="running")
        progress_bar.progress(40)
        
        # Listas para almacenar resultados
        poligonos_gee = []
        fallidos = []
        renspa_sin_poligono = []
        
        # Procesar cada RENSPA
        for i, item in enumerate(renspa_a_procesar):
            renspa = item['renspa']
            # Actualizar progreso
            progress_percentage = 40 + (i * 40 // len(renspa_a_procesar))
            progress_bar.progress(progress_percentage)
            status.write(f"Procesando RENSPA: {renspa} ({i+1}/{len(renspa_a_procesar)})")
            
            # Verificar si ya tiene el polígono en la información básica
            if 'poligono' in item and item['poligono']:
                poligono_str = item['poligono']
                superficie = item.get('superficie', 0)
                
                # Extraer coordenadas
                coordenadas = extraer_coordenadas(poligono_str)
                
                if coordenadas:
                    # Crear objeto con datos del polígono
                    poligono_data = {
                        'renspa': renspa,
                        'coords': coordenadas,
                        'superficie': superficie,
                        'titular': item.get('titular', ''),
                        'localidad': item.get('localidad', ''),
                        'cuit': cuit_normalizado
                    }
                    poligonos_gee.append(poligono_data)
                    continue
            
            # Si no tenía polígono o no era válido, consultar más detalles
            resultado = consultar_renspa_detalle(renspa)
            
            if resultado and 'items' in resultado and resultado['items'] and 'poligono' in resultado['items'][0]:
                item_detalle = resultado['items'][0]
                poligono_str = item_detalle.get('poligono')
                superficie = item_detalle.get('superficie', 0)
                
                if poligono_str:
                    # Extraer coordenadas
                    coordenadas = extraer_coordenadas(poligono_str)
                    
                    if coordenadas:
                        # Crear objeto con datos del polígono
                        poligono_data = {
                            'renspa': renspa,
                            'coords': coordenadas,
                            'superficie': superficie,
                            'titular': item.get('titular', ''),
                            'localidad': item.get('localidad', ''),
                            'cuit': cuit_normalizado
                        }
                        poligonos_gee.append(poligono_data)
                    else:
                        fallidos.append(renspa)
                else:
                    renspa_sin_poligono.append(renspa)
            else:
                renspa_sin_poligono.append(renspa)
            
            # Pausa breve para no sobrecargar la API
            time.sleep(TIEMPO_ESPERA)
        
        # Mostrar estadísticas
        total_procesados = len(renspa_a_procesar)
        total_exitosos = len(poligonos_gee)
        total_fallidos = len(fallidos)
        total_sin_poligono = len(renspa_sin_poligono)
        
        # Completar procesamiento
        status.update(label=f"Procesamiento completo. {total_exitosos} polígonos obtenidos", state="complete")
        progress_bar.progress(100)
    
    return df_renspa, poligonos_gee

# Función para procesar el análisis de cultivos
def analizar_cultivos(poligonos, campana):
    """
    Analiza los cultivos en los polígonos utilizando Google Earth Engine (simulado)
    
    Args:
        poligonos: Lista de polígonos a analizar
        campana: Campaña seleccionada
        
    Returns:
        cultivos_por_poligono: Diccionario con cultivos por polígono
        df_resumen: DataFrame con resumen de cultivos
    """
    # Mostrar indicador de procesamiento
    with st.status('Analizando cultivos con Google Earth Engine...', expanded=True) as status:
        # Progreso
        progress_bar = st.progress(0)
        
        # Paso 1: Enviar polígonos a GEE
        status.update(label="Enviando polígonos a Google Earth Engine...", state="running")
        progress_bar.progress(30)
        
        # Paso 2: Procesar análisis de cultivos
        status.update(label=f"Analizando cultivos para {campana}...", state="running")
        progress_bar.progress(60)
        
        # Simular consulta a GEE
        cultivos_por_poligono = consultar_gee_cultivos(poligonos, campana)
        
        # Generar resumen de cultivos
        status.update(label="Generando resumen de cultivos...", state="running")
        progress_bar.progress(80)
        
        df_resumen = generar_resumen_cultivos(poligonos, cultivos_por_poligono)
        
        # Completar procesamiento
        status.update(label="Análisis de cultivos completado", state="complete")
        progress_bar.progress(100)
    
    return cultivos_por_poligono, df_resumen

# Interfaz de usuario
st.title("Consulta RENSPA - SENASA & Google Earth Engine")

# Introducción
st.markdown("""
Esta herramienta permite:

1. Consultar RENSPA por CUIT desde SENASA
2. Visualizar polígonos de campos en mapa interactivo
3. Analizar cultivos de cada campaña agrícola usando Google Earth Engine
4. Ver estadísticas detalladas de uso de la tierra
""")

# Formulario de consulta
st.header("Consulta por CUIT")

with st.form("consulta_cuit_form"):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        cuit_input = st.text_input(
            "Ingrese el CUIT (formato: XX-XXXXXXXX-X o XXXXXXXXXXX):", 
            value="30-65425756-2"
        )
    
    with col2:
        solo_activos = st.checkbox("Solo RENSPA activos", value=True)
    
    submitted = st.form_submit_button("Consultar RENSPA")

# Procesar consulta
if submitted:
    # Limpiar estado anterior
    st.session_state.analisis_cultivos = False
    st.session_state.cultivos_por_poligono = {}
    
    try:
        # Procesar CUIT
        df_renspa, poligonos_gee = procesar_cuit(cuit_input, solo_activos)
        
        # Guardar en estado
        st.session_state.df_renspa = df_renspa
        st.session_state.poligonos_gee = poligonos_gee
        st.session_state.cuit_actual = cuit_input
        
    except Exception as e:
        st.error(f"Error durante el procesamiento: {str(e)}")

# Mostrar resultados si hay datos
if not st.session_state.df_renspa.empty:
    st.header("Resultados de la Consulta")
    
    # Mostrar tabla de RENSPA
    with st.expander("Listado de RENSPA", expanded=True):
        st.dataframe(st.session_state.df_renspa)
    
    # Mostrar mapa con polígonos (si hay)
    if st.session_state.poligonos_gee and folium_disponible:
        st.header("Visualización de Polígonos")
        
        # Mostrar mapa básico sin análisis de cultivos
        if not st.session_state.analisis_cultivos:
            # Crear mapa simple
            m = folium.Map(location=[-34.603722, -58.381592], zoom_start=10)
            
            # Agregar capas base con atribución
            folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                            name='Google Hybrid', 
                            attr='Google').add_to(m)
            folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                            name='Google Satellite', 
                            attr='Google').add_to(m)
            folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
            
            # Añadir herramienta de medición
            MeasureControl(position='topright', 
                          primary_length_unit='kilometers', 
                          secondary_length_unit='miles', 
                          primary_area_unit='hectares').add_to(m)
            
            # Añadir mini mapa para ubicación
            MiniMap().add_to(m)
            
            # Determinar centro del mapa
            all_lats = []
            all_lons = []
            for pol in st.session_state.poligonos_gee:
                for coord in pol['coords']:
                    all_lons.append(coord[0])
                    all_lats.append(coord[1])
            
            if all_lats and all_lons:
                center_lat = sum(all_lats) / len(all_lats)
                center_lon = sum(all_lons) / len(all_lons)
                m.fit_bounds([[min(all_lats), min(all_lons)], [max(all_lats), max(all_lons)]])
            
            # Crear grupo de capas para polígonos
            fg_poligonos = folium.FeatureGroup(name="Polígonos RENSPA").add_to(m)
            
            # Añadir cada polígono al mapa
            for pol in st.session_state.poligonos_gee:
                renspa = pol['renspa']
                
                # Información básica del polígono para popup
                popup_html = f"""
                <div style="width:250px;">
                    <h4>RENSPA: {renspa}</h4>
                    <p><b>Titular:</b> {pol.get('titular', 'No disponible')}</p>
                    <p><b>Localidad:</b> {pol.get('localidad', 'No disponible')}</p>
                    <p><b>Superficie:</b> {pol.get('superficie', 0)} ha</p>
                </div>
                """
                
                # Añadir polígono al mapa
                folium.Polygon(
                    locations=[[coord[1], coord[0]] for coord in pol['coords']],  # Invertir coordenadas para folium
                    color='red',
                    weight=2,
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.3,
                    tooltip=f"RENSPA: {renspa}",
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(fg_poligonos)
            
            # Añadir control de capas
            folium.LayerControl(position='topright').add_to(m)
            
            # Mostrar el mapa
            folium_static(m, width=1000, height=600)
            
            # Mostrar botón para análisis de cultivos
            st.header("Análisis de Cultivos")
            
            # Selección de campaña
            col1, col2 = st.columns([3, 1])
            
            with col1:
                campana = st.selectbox(
                    "Seleccionar campaña agrícola:",
                    ["Campaña 2019-2020", "Campaña 2020-2021", "Campaña 2021-2022", "Campaña 2022-2023", "Campaña 2023-2024"],
                    index=1  # Campaña 2020-2021 por defecto
                )
            
            with col2:
                # Botón para iniciar análisis
                if st.button("Analizar Cultivos con GEE"):
                    # Guardar selección de campaña
                    st.session_state.campana_seleccionada = campana
                    
                    # Realizar análisis
                    cultivos_por_poligono, df_resumen = analizar_cultivos(
                        st.session_state.poligonos_gee, 
                        campana
                    )
                    
                    # Guardar en estado
                    st.session_state.cultivos_por_poligono = cultivos_por_poligono
                    st.session_state.analisis_cultivos = True
                    
                    # Forzar recarga para mostrar resultados
                    st.experimental_rerun()
        
        # Mostrar mapa con análisis de cultivos
        else:
            # Crear mapa con cultivos
            m = crear_mapa_cultivos(
                st.session_state.poligonos_gee, 
                st.session_state.cultivos_por_poligono,
                st.session_state.campana_seleccionada
            )
            
            # Calcular superficie total
            superficie_total = sum(p.get('superficie', 0) for p in st.session_state.poligonos_gee)
            
            # Generar resumen
            df_resumen = generar_resumen_cultivos(
                st.session_state.poligonos_gee, 
                st.session_state.cultivos_por_poligono
            )
            
            # Crear leyenda estilo GEE
            leyenda_html = crear_leyenda_gee_cultivos(
                df_resumen, 
                superficie_total,
                st.session_state.campana_seleccionada
            )
            
            # Mostrar el mapa
            st.subheader(f"Análisis de Cultivos - {st.session_state.campana_seleccionada}")
            map_container = st.container()
            
            with map_container:
                folium_static(m, width=1000, height=600)
                
                # Mostrar la leyenda estilo GEE
                st.markdown(leyenda_html, unsafe_allow_html=True)
            
            # Mostrar tabla de resumen
            st.subheader("Resumen de Cultivos")
            
            # Agregar columna para formato de presentación
            df_resumen['Presentación'] = df_resumen.apply(
                lambda row: f"{int(row['Área (ha)'])} Ha ({int(row['Porcentaje (%)'])}%)", 
                axis=1
            )
            
            # Mostrar tabla
            st.dataframe(
                df_resumen[['Cultivo', 'Área (ha)', 'Porcentaje (%)', 'Presentación']],
                column_config={
                    "Cultivo": st.column_config.TextColumn("Cultivo"),
                    "Área (ha)": st.column_config.NumberColumn("Área (ha)", format="%.1f"),
                    "Porcentaje (%)": st.column_config.NumberColumn("Porcentaje (%)", format="%.1f"),
                    "Presentación": st.column_config.TextColumn("Formato GEE")
                },
                hide_index=True
            )
            
            # Mostrar gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras
                fig1, ax1 = plt.subplots(figsize=(8, 6))
                
                # Diccionario de colores por cultivo
                colores_cultivo = {
                    'Maíz': '#0042ff',         # Azul
                    'Soja 1ra': '#339820',     # Verde
                    'CI-Soja 2da': '#90ee90',  # Verde claro
                    'CI-Maíz 2da': '#87CEEB',  # Azul claro
                    'Arroz': '#1d1e33',        # Azul oscuro
                    'No agrícola': '#646b63',  # Gris
                    'Girasol': '#FFFF00',      # Amarillo
                    'Sorgo GR': '#FF0000',     # Rojo
                    'Algodón': '#b7b9bd',      # Gris claro
                    'Default': '#FF0000'       # Rojo (por defecto)
                }
                
                # Obtener colores para el gráfico
                colores = [colores_cultivo.get(cultivo, '#FF0000') for cultivo in df_resumen['Cultivo']]
                
                # Crear gráfico de barras
                ax1.bar(df_resumen['Cultivo'], df_resumen['Área (ha)'], color=colores)
                ax1.set_ylabel('Hectáreas')
                ax1.set_title(f'Distribución de Cultivos - {st.session_state.campana_seleccionada}')
                
                # Añadir etiquetas de valor encima de las barras
                for i, v in enumerate(df_resumen['Área (ha)']):
                    ax1.text(i, v + 5, f"{int(v)}", ha='center')
                
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig1)
            
            with col2:
                # Gráfico de torta
                fig2, ax2 = plt.subplots(figsize=(8, 8))
                
                # Crear gráfico de torta
                wedges, texts, autotexts = ax2.pie(
                    df_resumen['Área (ha)'], 
                    labels=df_resumen['Cultivo'], 
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colores,
                    explode=[0.05 if i == 0 else 0 for i in range(len(df_resumen))]
                )
                
                # Establecer propiedades del texto
                for text in texts:
                    text.set_fontsize(10)
                
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_color('white')
                
                ax2.axis('equal')  # Para que el gráfico sea circular
                ax2.set_title(f'Proporción de Cultivos - {st.session_state.campana_seleccionada}')
                
                plt.tight_layout()
                st.pyplot(fig2)
            
            # Botón para cambiar de campaña
            st.subheader("Cambiar Análisis")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                nueva_campana = st.selectbox(
                    "Seleccionar otra campaña agrícola:",
                    ["Campaña 2019-2020", "Campaña 2020-2021", "Campaña 2021-2022", "Campaña 2022-2023", "Campaña 2023-2024"],
                    index=["Campaña 2019-2020", "Campaña 2020-2021", "Campaña 2021-2022", "Campaña 2022-2023", "Campaña 2023-2024"].index(st.session_state.campana_seleccionada)
                )
            
            with col2:
                if st.button("Cambiar Campaña"):
                    # Guardar selección de campaña
                    st.session_state.campana_seleccionada = nueva_campana
                    
                    # Realizar análisis
                    cultivos_por_poligono, _ = analizar_cultivos(
                        st.session_state.poligonos_gee, 
                        nueva_campana
                    )
                    
                    # Guardar en estado
                    st.session_state.cultivos_por_poligono = cultivos_por_poligono
                    
                    # Forzar recarga para mostrar resultados
                    st.experimental_rerun()
            
            # Opción para volver a la visualización básica
            if st.button("Volver a Visualización Básica"):
                # Limpiar estado de análisis
                st.session_state.analisis_cultivos = False
                st.session_state.cultivos_por_poligono = {}
                
                # Forzar recarga
                st.experimental_rerun()
    
    elif not folium_disponible:
        st.warning("Para visualizar mapas, instale folium y streamlit-folium")
    
    else:
        st.warning("No se encontraron polígonos para visualizar")

# Pie de página
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado para análisis agrícola en Argentina")
st.sidebar.markdown("Integración con Google Earth Engine para análisis de cultivos")
