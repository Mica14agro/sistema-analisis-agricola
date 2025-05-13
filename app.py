import streamlit as st
import ee
import geemap
import json
import tempfile
import os
import webbrowser
import requests
from io import BytesIO
import pandas as pd

# Función para inicializar Earth Engine
def inicializar_earth_engine():
    """
    Inicializa Google Earth Engine y retorna True si fue exitoso
    """
    try:
        # Intentar inicializar con credenciales por defecto
        ee.Initialize()
        return True
    except Exception as e:
        st.error(f"Error al inicializar Earth Engine: {str(e)}")
        
        # Crear un botón para autenticar
        if st.button("Autenticar con Google Earth Engine"):
            try:
                ee.Authenticate()
                ee.Initialize()
                st.success("Autenticación exitosa con Google Earth Engine")
                st.rerun()  # Recargar la app
                return True
            except Exception as auth_e:
                st.error(f"Error durante la autenticación: {str(auth_e)}")
                return False
        
        return False

# Función para convertir polígonos RENSPA a formato GeoJSON
def convertir_poligonos_a_geojson(poligonos):
    """
    Convierte una lista de polígonos RENSPA a formato GeoJSON
    
    Args:
        poligonos: Lista de diccionarios con los datos de polígonos RENSPA
        
    Returns:
        Objeto GeoJSON como diccionario
    """
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for pol in poligonos:
        if 'coords' in pol and pol['coords']:
            # Crear un feature para este polígono
            feature = {
                "type": "Feature",
                "properties": {
                    "renspa": pol.get('renspa', ''),
                    "titular": pol.get('titular', ''),
                    "localidad": pol.get('localidad', ''),
                    "superficie": pol.get('superficie', 0),
                    "cuit": pol.get('cuit', '')
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [pol['coords']]
                }
            }
            
            geojson["features"].append(feature)
    
    return geojson

# Función para verificar el estado de Earth Engine y mostrar información
def mostrar_info_earth_engine_sidebar():
    """
    Muestra información sobre Google Earth Engine en la barra lateral
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("Google Earth Engine")
    
    # Verificar si Earth Engine está inicializado
    if 'ee_status' in st.session_state and st.session_state.ee_status.initialized:
        st.sidebar.success("✅ Google Earth Engine está activado")
        st.sidebar.info(
            "Puedes analizar cultivos históricos en campos RENSPA utilizando "
            "las imágenes satelitales de Google Earth Engine."
        )
    else:
        st.sidebar.warning("⚠️ Google Earth Engine no está activado")
        st.sidebar.info(
            "Para activar el análisis de cultivos históricos, haz clic en el botón 'Autenticar con Google Earth Engine' "
            "que aparecerá cuando consultes polígonos RENSPA."
        )
    
    # Mostrar créditos
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Datos de cultivos proporcionados por Google Earth Engine.\n\n"
        "Capas disponibles: 2019-2020 hasta 2023-2024."
    )

# Función para convertir GeoJSON a código JavaScript para Earth Engine
def geojson_a_codigo_ee(geojson_data):
    """
    Convierte un objeto GeoJSON a código JavaScript para Google Earth Engine
    
    Args:
        geojson_data: Objeto GeoJSON en formato diccionario
        
    Returns:
        Código JavaScript para definir el AOI en Earth Engine
    """
    js_code = []
    js_code.append("var aoi = ee.FeatureCollection([")
    
    if geojson_data.get('type') == 'FeatureCollection' and 'features' in geojson_data:
        features = geojson_data['features']
        
        # Procesar cada feature
        for i, feature in enumerate(features):
            geometry = feature.get('geometry', {})
            geometry_type = geometry.get('type')
            coordinates = geometry.get('coordinates', [])
            properties = feature.get('properties', {})
            
            # Agregar comentario para el feature
            js_code.append(f"  // Feature {i+1}")
            js_code.append("  ee.Feature(")
            
            # Agregar geometría según el tipo
            if geometry_type == 'Polygon':
                # Tomar el anillo exterior (primer elemento)
                coords_str = ", ".join([f"[{coord[0]}, {coord[1]}]" for coord in coordinates[0]])
                js_code.append(f"    ee.Geometry.Polygon([[{coords_str}]]),")
            else:
                js_code.append(f"    // Tipo de geometría no soportado: {geometry_type}")
                js_code.append("    ee.Geometry.Point([0, 0]),  // Geometría vacía")
            
            # Agregar propiedades
            props_list = []
            for key, value in properties.items():
                if isinstance(value, str):
                    props_list.append(f"'{key}': '{value}'")
                else:
                    props_list.append(f"'{key}': {value}")
            
            props_str = "{" + ", ".join(props_list) + "}"
            js_code.append(f"    {props_str}")
            
            # Cerrar el Feature
            if i < len(features) - 1:
                js_code.append("  ),")
            else:
                js_code.append("  )")
    
    # Cerrar la FeatureCollection
    js_code.append("]);")
    
    return "\n".join(js_code)

# Función para reemplazar la línea AOI en el código Earth Engine
def reemplazar_aoi_en_codigo(codigo_original, aoi_code):
    """
    Reemplaza la definición de AOI en el código original con el nuevo código
    
    Args:
        codigo_original: Código JavaScript original
        aoi_code: Nuevo código de definición de AOI
        
    Returns:
        Código actualizado
    """
    import re
    
    # Patrón para encontrar la línea del AOI
    pattern = r'var\s+aoi\s*=\s*ee\.FeatureCollection\([^\)]+\);'
    
    # Comprobar si el patrón existe en el código
    if re.search(pattern, codigo_original):
        # Reemplazar la línea encontrada con el nuevo código
        updated_code = re.sub(pattern, aoi_code, codigo_original)
        return updated_code
    else:
        # Si no se encuentra la línea, buscar otra definición más simple de aoi
        alt_pattern = r'var\s+aoi\s*=.*?;'
        if re.search(alt_pattern, codigo_original):
            updated_code = re.sub(alt_pattern, aoi_code, codigo_original)
            return updated_code
        else:
            # Si no se encuentra ninguna definición, insertar el nuevo código al principio
            return aoi_code + "\n\n" + codigo_original

# Función para generar un archivo HTML con el código Earth Engine integrado
def generar_html_earth_engine(js_code):
    """
    Genera un archivo HTML con el código de Earth Engine incrustado
    
    Args:
        js_code: Código JavaScript de Earth Engine
        
    Returns:
        Ruta al archivo HTML generado
    """
    html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis de Cultivos - Earth Engine</title>
    <script src="https://code.earthengine.google.com/javascript/ee_api_js.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { width: 100%; height: 100vh; }
        .info-panel {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
            max-width: 350px;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h2>Análisis de Cultivos por Campaña</h2>
        <p>Analizando polígonos de RENSPA...</p>
        <p>Este análisis muestra los cultivos detectados en las diferentes campañas agrícolas.</p>
    </div>

    <script>
    // Inicializar Earth Engine con tu código
    function initMap() {
        ee.initialize(
            null, 
            null, 
            function() {
                // Tu código Earth Engine aquí
                %s
                
                // Asegurar que el mapa está centrado en el AOI
                Map.centerObject(aoi, 10);
                
                // Mensaje de éxito
                console.log('Earth Engine inicializado correctamente');
            },
            function(e) {
                console.error('Error al inicializar Earth Engine', e);
                alert('Error al inicializar Earth Engine: ' + e);
            }
        );
    }
    
    window.onload = initMap;
    </script>
</body>
</html>
    """ % js_code
    
    # Crear un archivo temporal para el HTML
    fd, path = tempfile.mkstemp(suffix='.html')
    with os.fdopen(fd, 'w') as f:
        f.write(html_template)
    
    return path

# Función para abrir análisis de Earth Engine en una nueva pestaña
def abrir_analisis_earth_engine(poligonos, codigo_ee_base):
    """
    Prepara y abre un análisis de Earth Engine en una nueva pestaña
    
    Args:
        poligonos: Lista de polígonos RENSPA
        codigo_ee_base: Código base de Earth Engine
        
    Returns:
        True si se pudo abrir, False en caso contrario
    """
    try:
        # Convertir polígonos a GeoJSON
        geojson_data = convertir_poligonos_a_geojson(poligonos)
        
        # Verificar que hay polígonos para analizar
        if not geojson_data['features']:
            st.error("No hay polígonos válidos para analizar.")
            return False
        
        # Convertir GeoJSON a código de Earth Engine
        aoi_code = geojson_a_codigo_ee(geojson_data)
        
        # Reemplazar AOI en el código base
        codigo_actualizado = reemplazar_aoi_en_codigo(codigo_ee_base, aoi_code)
        
        # Generar HTML con el código
        html_path = generar_html_earth_engine(codigo_actualizado)
        
        # Abrir en el navegador
        webbrowser.open('file://' + html_path)
        
        return True
    
    except Exception as e:
        st.error(f"Error al preparar el análisis de Earth Engine: {str(e)}")
        return False

# Código base de Earth Engine para análisis de cultivos
CODIGO_EARTH_ENGINE_BASE = """
// CÓDIGO UNIFICADO PARA ANÁLISIS DE CULTIVOS POR CAMPAÑA
// Este script permite analizar diferentes capas de cultivos sobre áreas específicas
// y comparar entre campañas agrícolas (2019-2020 hasta 2023-2024)


// ===== CONFIGURACIÓN DE CAPAS Y ÁREAS =====


// Cargar el AOI (área de interés)
var aoi = ee.FeatureCollection('projects/scanvel/assets/FontIsabelPoligonos');


// Calcular el área total del AOI en hectáreas
var areaTotalAOI = aoi.geometry().area().divide(10000);


// Calcular el área de cada píxel en metros cuadrados
var areaPixeles = ee.Image.pixelArea();


// Centrar el mapa en el AOI
Map.centerObject(aoi, 10);

// ===== CONFIGURACIÓN CAMPAÑA 2019-2020 =====
// Cargar las capas de cultivos 2019-2020
var inv19 = ee.Image('projects/scanvel/assets/inv19');
var ver20 = ee.Image('projects/scanvel/assets/ver20');


// Recortar las capas al AOI
var inv19_aoi = inv19.clip(aoi);
var ver20_aoi = ver20.clip(aoi);


// Crear una capa combinada para 2019-2020 (CORREGIDO)
var capa1920 = ee.Image().expression(
 '(verano == 10 && (invierno == 0 || invierno == 6)) ? 31 : ' + // CI-Maíz
 '(verano == 11 && (invierno == 0 || invierno == 6)) ? 32 : ' + // CI-Soja
 '(verano == 10) ? 10 : ' + // Maíz
 '(verano == 11) ? 11 : ' + // Soja 1ra
 '(verano == 14) ? 14 : ' + // Caña de azúcar es 14 (corregido)
 '(verano == 19) ? 19 : ' + // Girasol-CV es 19
 'verano', // Para otros cultivos
 {
   'verano': ver20_aoi,
   'invierno': inv19_aoi
 }
);


// Definir nombres de cultivos para la capa 2019-2020 (CORREGIDO)
var cultivos_1920 = {
 10: 'Maíz',
 11: 'Soja 1ra',
 12: 'Girasol',
 13: 'Poroto',
 14: 'Caña de azúcar', // Asegurando que 14 es Caña
 15: 'Algodón',
 16: 'Maní',
 17: 'Arroz',
 18: 'Sorgo GR',
 19: 'Girasol-CV', // Asegurando que 19 es Girasol-CV
 21: 'No agrícola',
 22: 'No agrícola',
 31: 'CI-Maíz 2da',
 32: 'CI-Soja 2da'
};


// Definir la paleta de colores para la capa 2019-2020
var paleta1920 = {
 10: '#0042ff', // Maíz (Azul)
 11: '#339820', // Soja 1ra (Verde)
 12: '#FFFF00', // Girasol (Amarillo)
 13: '#f022db', // Poroto (Rosa)
 14: '#a32102', // Caña de azúcar (Rojo oscuro) - Corregido
 15: '#b7b9bd', // Algodón (Gris)
 16: '#FFA500', // Maní (Naranja)
 17: '#1d1e33', // Arroz
 18: '#FF0000', // Sorgo GR (Rojo)
 19: '#a32102', // Girasol-CV (Rojo oscuro) - mismo color que caña para consistencia
 21: '#646b63', // Barbecho
 22: '#e6f0c2', // No agrícola
 31: '#87CEEB', // CI-Maíz 2da (Azul claro/celeste)
 32: '#90ee90'  // CI-Soja 2da (Verde claro/fluor)
};


// Convertir el objeto de paleta a un array para visualización
var paleta1920Array = [];
var maxValor1920 = 32;
for (var i = 0; i <= maxValor1920; i++) {
 paleta1920Array[i] = paleta1920[i] || '#ffffff'; // Blanco para valores no definidos
}

// ===== CONFIGURACIÓN CAMPAÑA 2020-2021 =====
// Cargar las capas de cultivos 2020-2021
var inv20 = ee.Image('projects/scanvel/assets/inv20');
var ver21 = ee.Image('projects/scanvel/assets/ver21');


// Recortar las capas al AOI
var inv20_aoi = inv20.clip(aoi);
var ver21_aoi = ver21.clip(aoi);


// Crear una capa combinada para 2020-2021 (CORREGIDO)
var capa2021 = ee.Image().expression(
 '(verano == 10 && (invierno == 0 || invierno == 16 || invierno == 24)) ? 31 : ' + // CI-Maíz
 '(verano == 11 && (invierno == 0 || invierno == 16 || invierno == 24)) ? 32 : ' + // CI-Soja
 '(verano == 10) ? 10 : ' + // Maíz
 '(verano == 11) ? 11 : ' + // Soja 1ra
 '(verano == 14) ? 14 : ' + // Caña de azúcar es 14 (corregido)
 '(verano == 19) ? 19 : ' + // Girasol-CV es 19
 '(verano == 26) ? 26 : ' + // Papa es 26
 'verano', // Para otros cultivos
 {
   'verano': ver21_aoi,
   'invierno': inv20_aoi
 }
);


// Definir nombres de cultivos para la capa 2020-2021 (CORREGIDO)
var cultivos_2021 = {
 10: 'Maíz',
 11: 'Soja 1ra',
 12: 'Girasol',
 13: 'Poroto',
 14: 'Caña de azúcar', // Asegurando que 14 es Caña
 15: 'Algodón',
 16: 'Maní',
 17: 'Arroz',
 18: 'Sorgo GR',
 19: 'Girasol-CV', // Asegurando que 19 es Girasol-CV
 21: 'No agrícola',
 22: 'No agrícola',
 26: 'Papa',
 28: 'Verdeo de Sorgo',
 31: 'CI-Maíz 2da',
 32: 'CI-Soja 2da'
};


// Definir la paleta de colores para la capa 2020-2021
var paleta2021 = {
 10: '#0042ff', // Maíz (Azul)
 11: '#339820', // Soja 1ra (Verde)
 12: '#FFFF00', // Girasol (Amarillo)
 13: '#f022db', // Poroto
 14: '#a32102', // Caña de azúcar (Rojo oscuro) - Corregido
 15: '#b7b9bd', // Algodón
 16: '#FFA500', // Maní (Naranja)
 17: '#1d1e33', // Arroz
 18: '#FF0000', // Sorgo GR (Rojo)
 19: '#a32102', // Girasol-CV (Rojo oscuro) - mismo color que caña para consistencia
 21: '#646b63', // No agrícola
 22: '#e6f0c2', // No agrícola
 26: '#8A2BE2', // Papa (Violeta)
 28: '#800080', // Verdeo de Sorgo (Morado)
 31: '#87CEEB', // CI-Maíz (Azul claro/celeste)
 32: '#90ee90'  // CI-Soja (Verde claro/fluor)
};


// Convertir el objeto de paleta a un array para visualización
var paleta2021Array = [];
var maxValor2021 = 32;
for (var i = 0; i <= maxValor2021; i++) {
 paleta2021Array[i] = paleta2021[i] || '#ffffff'; // Blanco para valores no definidos
}

// ===== CONFIGURACIÓN CAMPAÑA 2021-2022 =====
// Cargar las capas de cultivos 2021-2022
var inv21 = ee.Image('projects/scanvel/assets/inv21');
var ver22 = ee.Image('projects/scanvel/assets/ver22');


// Recortar las capas al AOI
var inv21_aoi = inv21.clip(aoi);
var ver22_aoi = ver22.clip(aoi);


// Crear una capa combinada para 2021-2022 (CORREGIDO)
var capa2122 = ee.Image().expression(
 '(verano == 10 && (invierno == 6 || invierno == 16 || invierno == 24)) ? 31 : ' + // CI-Maíz
 '(verano == 11 && (invierno == 6 || invierno == 16 || invierno == 24)) ? 32 : ' + // CI-Soja
 '(verano == 10) ? 10 : ' + // Maíz
 '(verano == 11) ? 11 : ' + // Soja 1ra
 '(invierno == 19 || verano == 14) ? 14 : ' + // Caña de azúcar si es 19 en invierno o 14 en verano
 '(verano == 19) ? 19 : ' + // Girasol-CV si es 19 en verano
 '(verano == 26) ? 26 : ' + // Papa es 26
 'verano', // Para otros cultivos
 {
   'verano': ver22_aoi,
   'invierno': inv21_aoi
 }
);


// Definir nombres de cultivos para la capa 2021-2022 (CORREGIDO)
var cultivos_2122 = {
 10: 'Maíz',
 11: 'Soja 1ra',
 12: 'Girasol',
 13: 'Poroto',
 14: 'Caña de azúcar', // Corregido
 15: 'Algodón',
 16: 'Maní',
 17: 'Arroz',
 18: 'Sorgo GR',
 19: 'Girasol-CV', // Asegurando que está presente
 21: 'No agrícola',
 22: 'No agrícola',
 26: 'Papa',
 28: 'Verdeo de Sorgo',
 31: 'CI-Maíz 2da',
 32: 'CI-Soja 2da'
};


// Definir la paleta de colores para la capa 2021-2022
var paleta2122 = {
 10: '#0042ff', // Maíz (Azul)
 11: '#339820', // Soja 1ra (Verde)
 12: '#FFFF00', // Girasol (Amarillo)
 13: '#f022db', // Poroto
 14: '#a32102', // Caña de azúcar (Rojo oscuro) - Corregido
 15: '#b7b9bd', // Algodón
 16: '#FFA500', // Maní (Naranja)
 17: '#1d1e33', // Arroz
 18: '#FF0000', // Sorgo GR (Rojo)
 19: '#a32102', // Girasol-CV (Rojo oscuro) - mismo color que caña para consistencia
 21: '#646b63', // No agrícola
 22: '#e6f0c2', // No agrícola
 26: '#8A2BE2', // Papa (Violeta)
 28: '#800080', // Verdeo de Sorgo (Morado)
 31: '#87CEEB', // CI-Maíz (Azul claro/celeste)
 32: '#90ee90'  // CI-Soja (Verde claro/fluor)
};


// Convertir el objeto de paleta a un array para visualización
var paleta2122Array = [];
var maxValor2122 = 32;
for (var i = 0; i <= maxValor2122; i++) {
 paleta2122Array[i] = paleta2122[i] || '#ffffff'; // Blanco para valores no definidos
}


// ===== CONFIGURACIÓN CAMPAÑA 2022-2023 =====
// Cargar las capas de cultivos 2022-2023
var inv22 = ee.Image('projects/scanvel/assets/inv22');
var ver23 = ee.Image('projects/scanvel/assets/ver23');


// Recortar las capas al AOI
var inv22_aoi = inv22.clip(aoi);
var ver23_aoi = ver23.clip(aoi);


// Crear una capa combinada para 2022-2023 (CORREGIDO)
var capa2223 = ee.Image().expression(
 '(verano == 10 && (invierno == 6 || invierno == 16 || invierno == 24)) ? 31 : ' + // CI-Maíz
 '(verano == 11 && (invierno == 6 || invierno == 16 || invierno == 24)) ? 32 : ' + // CI-Soja
 '(verano == 10) ? 10 : ' + // Maíz
 '(verano == 11) ? 11 : ' + // Soja 1ra
 '(invierno == 19 || verano == 14) ? 14 : ' + // Caña de azúcar si es 19 en invierno o 14 en verano
 '(verano == 19) ? 19 : ' + // Girasol-CV si es 19 en verano
 '(verano == 26) ? 26 : ' + // Papa es 26
 'verano', // Para otros cultivos
 {
   'verano': ver23_aoi,
   'invierno': inv22_aoi
 }
);


// Definir nombres de cultivos para la capa 2022-2023 (CORREGIDO)
var cultivos_2223 = {
 10: 'Maíz',
 11: 'Soja 1ra',
 12: 'Girasol',
 13: 'Poroto',
 14: 'Caña de azúcar', // Corregido
 15: 'Algodón',
 16: 'Maní',
 17: 'Arroz',
 18: 'Sorgo GR',
 19: 'Girasol-CV', // Asegurando que está presente
 21: 'No agrícola',
 22: 'No agrícola',
 26: 'Papa',
 28: 'Verdeo de Sorgo',
 30: 'Tabaco',
 31: 'CI-Maíz 2da',
 32: 'CI-Soja 2da'
};


// Definir la paleta de colores para la capa 2022-2023
var paleta2223 = {
 10: '#0042ff', // Maíz (Azul)
 11: '#339820', // Soja 1ra (Verde)
 12: '#FFFF00', // Girasol (Amarillo)
 13: '#f022db', // Poroto
 14: '#a32102', // Caña de azúcar (Rojo oscuro) - Corregido
 15: '#b7b9bd', // Algodón
 16: '#FFA500', // Maní (Naranja)
 17: '#1d1e33', // Arroz
 18: '#FF0000', // Sorgo GR (Rojo)
 19: '#a32102', // Girasol-CV (Rojo oscuro) - mismo color que caña para consistencia
 21: '#646b63', // No agrícola
 22: '#e6f0c2', // No agrícola
 26: '#8A2BE2', // Papa (Violeta)
 28: '#800080', // Verdeo de Sorgo (Morado)
 30: '#D2B48C', // Tabaco (Marrón claro)
 31: '#87CEEB', // CI-Maíz (Azul claro/celeste)
 32: '#90ee90'  // CI-Soja (Verde claro/fluor)
};


// Convertir el objeto de paleta a un array para visualización
var paleta2223Array = [];
var maxValor2223 = 32;
for (var i = 0; i <= maxValor2223; i++) {
 paleta2223Array[i] = paleta2223[i] || '#ffffff'; // Blanco para valores no definidos
}
// ===== CONFIGURACIÓN CAMPAÑA 2023-2024 =====
// Cargar las capas de cultivos 2023-2024
var inv23 = ee.Image('projects/scanvel/assets/inv23');
var ver24 = ee.Image('projects/scanvel/assets/ver24');


// Recortar las capas al AOI
var inv23_aoi = inv23.clip(aoi);
var ver24_aoi = ver24.clip(aoi);


// Crear una capa combinada para 2023-2024 (CORREGIDO)
var capa2324 = ee.Image().expression(
 '(verano == 10 && (invierno == 6 || invierno == 16 || invierno == 24)) ? 31 : ' + // CI-Maíz
 '(verano == 11 && (invierno == 6 || invierno == 16 || invierno == 24)) ? 32 : ' + // CI-Soja
 '(verano == 10) ? 10 : ' + // Maíz
 '(verano == 11) ? 11 : ' + // Soja 1ra
 '(invierno == 19 || verano == 14) ? 14 : ' + // Caña de azúcar si es 19 en invierno o 14 en verano
 '(verano == 19) ? 19 : ' + // Girasol-CV si es 19 en verano
 '(verano == 26) ? 26 : ' + // Papa es 26
 'verano', // Para otros cultivos
 {
   'verano': ver24_aoi,
   'invierno': inv23_aoi
 }
);


// Definir nombres de cultivos para la capa 2023-2024 (CORREGIDO)
var cultivos_2324 = {
 10: 'Maíz',
 11: 'Soja 1ra',
 12: 'Girasol',
 13: 'Poroto',
 14: 'Caña de azúcar', // Corregido
 15: 'Algodón',
 16: 'Maní',
 17: 'Arroz',
 18: 'Sorgo GR',
 19: 'Girasol-CV', // Asegurando que está presente
 21: 'No agrícola',
 22: 'No agrícola',
 26: 'Papa',
 28: 'Verdeo de Sorgo',
 30: 'Tabaco',
 31: 'CI-Maíz 2da',
 32: 'CI-Soja 2da'
};


// Definir la paleta de colores para la capa 2023-2024
var paleta2324 = {
 10: '#0042ff', // Maíz (Azul)
 11: '#339820', // Soja 1ra (Verde)
 12: '#FFFF00', // Girasol (Amarillo)
 13: '#f022db', // Poroto
 14: '#a32102', // Caña de azúcar (Rojo oscuro) - Corregido
 15: '#b7b9bd', // Algodón
 16: '#FFA500', // Maní (Naranja)
 17: '#1d1e33', // Arroz
 18: '#FF0000', // Sorgo GR (Rojo)
 19: '#a32102', // Girasol-CV (Rojo oscuro) - mismo color que caña para consistencia
 21: '#646b63', // No agrícola
 22: '#e6f0c2', // No agrícola
 26: '#8A2BE2', // Papa (Violeta)
 28: '#800080', // Verdeo de Sorgo (Morado)
 30: '#D2B48C', // Tabaco (Marrón claro)
 31: '#87CEEB', // CI-Maíz (Azul claro/celeste)
 32: '#90ee90'  // CI-Soja (Verde claro/fluor)
};


// Convertir el objeto de paleta a un array para visualización
var paleta2324Array = [];
var maxValor2324 = 32;
for (var i = 0; i <= maxValor2324; i++) {
 paleta2324Array[i] = paleta2324[i] || '#ffffff'; // Blanco para valores no definidos
}
// ===== FUNCIONES DE ANÁLISIS =====


// Función para calcular áreas y porcentajes
function calcularAreas(capa, cultivos, nombreCampana) {
 var areasCultivos = [];


 // Calcular áreas y porcentajes
 Object.keys(cultivos).forEach(function(cultivoId) {
   var idCultivo = parseInt(cultivoId);
   var nombre = cultivos[cultivoId];
  
   // Si el nombre es "XXX", omitir
   if (nombre === 'XXX') {
     return;
   }


   // Crear máscara para el cultivo
   var mascaraCultivo = capa.eq(idCultivo);


   // Calcular área del cultivo
   var areaCultivo = areaPixeles.multiply(mascaraCultivo).reduceRegion({
     reducer: ee.Reducer.sum(),
     geometry: aoi.geometry(),
     scale: 30, // Resolución de 30 metros
     maxPixels: 1e13
   }).get('area');


   // Convertir a hectáreas y redondear a entero
   areaCultivo = ee.Number(areaCultivo).divide(10000).round();


   // Calcular porcentaje respecto al AOI
   var porcentajeCultivo = areaCultivo.divide(areaTotalAOI).multiply(100).round();


   // Añadir a la lista
   areasCultivos.push({
     'Campaña': nombreCampana,
     'Cultivo': nombre,
     'Área (ha)': areaCultivo,
     'Porcentaje (%)': porcentajeCultivo,
     'ID': idCultivo  // Guardar el ID para asignación de colores
   });
 });


 return areasCultivos;
}


// Función para crear leyenda
function crearLeyenda(resultados, nombreCampana, posicion) {
 // Ordenar las áreas de mayor a menor
 resultados.sort(function(a, b) {
   return b['Área (ha)'] - a['Área (ha)'];
 });


 // Crear la leyenda
 var legend = ui.Panel({
   style: {
     position: posicion,
     padding: '8px 15px',
     backgroundColor: 'white',
     border: '1px solid #ccc'
   }
 });


 var legendTitle = ui.Label({
   value: 'Campaña ' + nombreCampana,
   style: {
     fontWeight: 'bold',
     fontSize: '18px',
     margin: '0 0 4px 0',
     padding: '0'
   }
 });
 legend.add(legendTitle);


 // Añadir cada cultivo y su área a la leyenda
 resultados.forEach(function(item) {
   var nombre = item['Cultivo'];
   var area = item['Área (ha)'];
   var porcentaje = item['Porcentaje (%)'];
   var idCultivo = item['ID'];
  
   var color;
   if (nombreCampana === '19-20') {
     color = paleta1920[idCultivo];
   } else if (nombreCampana === '20-21') {
     color = paleta2021[idCultivo];
   } else if (nombreCampana === '21-22') {
     color = paleta2122[idCultivo];
   } else if (nombreCampana === '22-23') {
     color = paleta2223[idCultivo];
   } else if (nombreCampana === '23-24') {
     color = paleta2324[idCultivo];
   }


   if (area >= 1) { // Solo agregar a la leyenda si el área es >= 1 Ha
     var legendItem = ui.Panel({
       widgets: [
         ui.Label({
           style: {backgroundColor: color, padding: '8px', margin: '0 0 4px 0'}
         }),
         ui.Label({
           value: nombre + ' ' + (area || 0) + ' Ha (' + (porcentaje || 0) + '%)',
           style: {margin: '0 0 0 8px'}
         })
       ],
       layout: ui.Panel.Layout.flow('horizontal')
     });


     legend.add(legendItem);
   }
 });


 return legend;
}
// ===== INTERFAZ DE USUARIO =====


// Panel principal para la interfaz
var panel = ui.Panel({
 style: {
   width: '350px',
   padding: '10px'
 }
});


// Título del panel
var title = ui.Label({
 value: 'Análisis de Cultivos por Campaña',
 style: {
   fontSize: '20px',
   fontWeight: 'bold',
   margin: '10px 0'
 }
});
panel.add(title);


// Crear selector de campaña
var campanaLabel = ui.Label('Seleccionar campaña:');
panel.add(campanaLabel);


var campanaSelector = ui.Select({
 items: [
   {label: 'Campaña 2019-2020', value: '19-20'},
   {label: 'Campaña 2020-2021', value: '20-21'},
   {label: 'Campaña 2021-2022', value: '21-22'},
   {label: 'Campaña 2022-2023', value: '22-23'},
   {label: 'Campaña 2023-2024', value: '23-24'}
 ],
 placeholder: 'Seleccione una campaña',
 onChange: function(campana) {
   actualizarVisualizacion(campana);
 }
});
panel.add(campanaSelector);


// Botón para exportar resultados
var exportButton = ui.Button({
 label: 'Exportar todos los resultados a CSV',
 onClick: function() {
   exportarResultados();
 }
});
panel.add(exportButton);


// Añadir el panel al mapa
ui.root.add(panel);


// Mostrar información del AOI
var infoPanel = ui.Panel({
 style: {
   position: 'bottom-left',
   padding: '8px 15px',
   backgroundColor: 'white',
   border: '1px solid #ccc'
 }
});


var infoTitle = ui.Label({
 value: 'Información del Área',
 style: {
   fontWeight: 'bold',
   fontSize: '16px',
   margin: '0 0 4px 0'
 }
});
infoPanel.add(infoTitle);


var areaLabel = ui.Label('Área total: ' + areaTotalAOI.getInfo().toFixed(2) + ' hectáreas');
infoPanel.add(areaLabel);


Map.add(infoPanel);
// ===== FUNCIONES PARA MANEJAR LA INTERFAZ =====


// Variable para guardar la leyenda actual
var leyendaActual = null;


// Función para actualizar la visualización
function actualizarVisualizacion(campana) {
 // Limpiar capas anteriores
 Map.layers().reset();
  // Si hay una leyenda existente, eliminarla
 if (leyendaActual) {
   Map.remove(leyendaActual);
   leyendaActual = null;
 }
  // Mostrar la capa de AOI
 Map.addLayer(aoi, {color: 'red'}, 'Área de Interés');
  // Dependiendo de la campaña, mostrar la capa correspondiente
 if (campana === '19-20') {
   Map.addLayer(capa1920, {min: 0, max: 32, palette: paleta1920Array, opacity: 0.7}, 'Cultivos 2019-2020');
  
   // Calcular áreas y crear leyenda
   var resultados1920 = [];
   ee.List(calcularAreas(capa1920, cultivos_1920, '19-20')).evaluate(function(result) {
     resultados1920 = result;
     leyendaActual = crearLeyenda(resultados1920, '19-20', 'bottom-right');
     Map.add(leyendaActual);
   });
 } else if (campana === '20-21') {
   Map.addLayer(capa2021, {min: 0, max: 32, palette: paleta2021Array, opacity: 0.7}, 'Cultivos 2020-2021');
  
   // Calcular áreas y crear leyenda
   var resultados2021 = [];
   ee.List(calcularAreas(capa2021, cultivos_2021, '20-21')).evaluate(function(result) {
     resultados2021 = result;
     leyendaActual = crearLeyenda(resultados2021, '20-21', 'bottom-right');
     Map.add(leyendaActual);
   });
 } else if (campana === '21-22') {
   Map.addLayer(capa2122, {min: 0, max: 32, palette: paleta2122Array, opacity: 0.7}, 'Cultivos 2021-2022');
  
   // Calcular áreas y crear leyenda
   var resultados2122 = [];
   ee.List(calcularAreas(capa2122, cultivos_2122, '21-22')).evaluate(function(result) {
     resultados2122 = result;
     leyendaActual = crearLeyenda(resultados2122, '21-22', 'bottom-right');
     Map.add(leyendaActual);
   });
 } else if (campana === '22-23') {
   Map.addLayer(capa2223, {min: 0, max: 32, palette: paleta2223Array, opacity: 0.7}, 'Cultivos 2022-2023');
  
   // Calcular áreas y crear leyenda
   var resultados2223 = [];
   ee.List(calcularAreas(capa2223, cultivos_2223, '22-23')).evaluate(function(result) {
     resultados2223 = result;
     leyendaActual = crearLeyenda(resultados2223, '22-23', 'bottom-right');
     Map.add(leyendaActual);
   });
 } else if (campana === '23-24') {
   Map.addLayer(capa2324, {min: 0, max: 32, palette: paleta2324Array, opacity: 0.7}, 'Cultivos 2023-2024');
  
   // Calcular áreas y crear leyenda
   var resultados2324 = [];
   ee.List(calcularAreas(capa2324, cultivos_2324, '23-24')).evaluate(function(result) {
     resultados2324 = result;
     leyendaActual = crearLeyenda(resultados2324, '23-24', 'bottom-right');
     Map.add(leyendaActual);
   });
 }
}


// Función para exportar todos los resultados a CSV
function exportarResultados() {
 // Calcular áreas para todas las campañas
 var resultados1920 = ee.List(calcularAreas(capa1920, cultivos_1920, '19-20'));
 var resultados2021 = ee.List(calcularAreas(capa2021, cultivos_2021, '20-21'));
 var resultados2122 = ee.List(calcularAreas(capa2122, cultivos_2122, '21-22'));
 var resultados2223 = ee.List(calcularAreas(capa2223, cultivos_2223, '22-23'));
 var resultados2324 = ee.List(calcularAreas(capa2324, cultivos_2324, '23-24'));
  // Combinar los resultados
 var todosResultados = resultados1920
   .cat(resultados2021)
   .cat(resultados2122)
   .cat(resultados2223)
   .cat(resultados2324);
  // Preparar para la exportación
 var featureCollection = ee.FeatureCollection(todosResultados.map(function(item) {
   return ee.Feature(null, item);
 }));
  // Exportar a CSV
 Export.table.toDrive({
   collection: featureCollection,
   description: 'Analisis_Cultivos_' + Date.now(),
   fileFormat: 'CSV'
 });
  // Notificar al usuario
 print('Iniciando exportación... Revise la pestaña "Tasks" para descargar el archivo CSV cuando esté listo.');
}


// Mensaje inicial
print('Seleccione una campaña del menú desplegable para visualizar los cultivos');
print('Área total del AOI (hectáreas):', areaTotalAOI);
// ===== FUNCIÓN PARA CALCULAR ESTADÍSTICAS DETALLADAS =====


// Función para calcular estadísticas detalladas de cultivos
function calcularEstadisticasDetalladas() {
 // Categorías consideradas "No Agrícolas" (CORREGIDO)
 var categoriasNoAgricolas = ['No Agrícola', 'No agrícola', 'Barbecho'];
  // Función auxiliar para verificar si un elemento está en un array
 function estaEnArray(elemento, array) {
   return array.indexOf(elemento) !== -1;
 }
  // Calcular áreas para todas las campañas
 var resultados1920 = calcularAreas(capa1920, cultivos_1920, '19-20');
 var resultados2021 = calcularAreas(capa2021, cultivos_2021, '20-21');
 var resultados2122 = calcularAreas(capa2122, cultivos_2122, '21-22');
 var resultados2223 = calcularAreas(capa2223, cultivos_2223, '22-23');
 var resultados2324 = calcularAreas(capa2324, cultivos_2324, '23-24');
  // Procesar todas las campañas
 ee.List([resultados1920, resultados2021, resultados2122, resultados2223, resultados2324])
   .evaluate(function(todasLasCampanas) {
     // Área total del AOI en hectáreas
     var areaTotal = areaTotalAOI.getInfo();
    
     // Estructura para almacenar datos por campaña
     var campanas = {
       '19-20': {},
       '20-21': {},
       '21-22': {},
       '22-23': {},
       '23-24': {}
     };
    
     // Procesamos cada campaña
     var campanasArray = ['19-20', '20-21', '21-22', '22-23', '23-24'];
    
     // Para seguimiento de todos los cultivos que aparecen
     var todosCultivos = [];
    
     // Procesar los resultados de cada campaña
     for (var i = 0; i < campanasArray.length; i++) {
       var nombreCampana = campanasArray[i];
       var resultadosCampana = todasLasCampanas[i] || [];
       var campanaData = campanas[nombreCampana];
      
       // Inicializar categorías principales
       campanaData['Agrícola'] = 0;
       campanaData['No Agrícola'] = 0;
      
       // Procesar cada cultivo
       for (var j = 0; j < resultadosCampana.length; j++) {
         var item = resultadosCampana[j];
         if (!item) continue;
        
         var nombreCultivo = item['Cultivo'];
         var area = item['Área (ha)'] || 0;
         var porcentaje = item['Porcentaje (%)'] || 0;
        
         // Normalizar nombres similares
         if (nombreCultivo === 'Caña' || nombreCultivo === 'Caña de Azúcar' || nombreCultivo === 'Caña de azúcar') {
           nombreCultivo = 'Caña de azúcar';
         }
        
         // Agregar a la lista de todos los cultivos si no existe
         if (todosCultivos.indexOf(nombreCultivo) === -1) {
           todosCultivos.push(nombreCultivo);
         }
        
         // Guardar datos del cultivo
         campanaData[nombreCultivo] = {
           area: area,
           porcentaje: porcentaje
         };
        
         // Sumar a la categoría correspondiente
         if (estaEnArray(nombreCultivo, categoriasNoAgricolas)) {
           campanaData['No Agrícola'] += area;
         } else {
           campanaData['Agrícola'] += area;
         }
       }
      
       // Calcular el área total detectada
       var areaDetectada = campanaData['Agrícola'] + campanaData['No Agrícola'];
      
       // Si hay diferencia con el área total, ajustar No Agrícola
       var diferencia = areaTotal - areaDetectada;
       if (diferencia > 0) {
         campanaData['No Agrícola'] += diferencia;
        
         // También agregamos una entrada para "Sin clasificar" si hay diferencia
         campanaData['Sin clasificar'] = {
           area: diferencia,
           porcentaje: Math.round((diferencia / areaTotal * 100))
         };
        
         // Agregar "Sin clasificar" a la lista de cultivos si no existe
         if (todosCultivos.indexOf('Sin clasificar') === -1) {
           todosCultivos.push('Sin clasificar');
         }
       }
      
       // Calcular porcentajes para las categorías principales
       campanaData['% Agrícola'] = Math.round((campanaData['Agrícola'] / areaTotal * 100));
       campanaData['% No Agrícola'] = Math.round((campanaData['No Agrícola'] / areaTotal * 100));
     }
    
     // Ordenar: primero No Agrícola, luego los cultivos principales solicitados, luego el resto
     var cultivosPrincipales = [
       'No Agrícola', 'Soja 1ra', 'Maíz', 'CI-Soja 2da', 'CI-Maíz 2da',
       'Girasol', 'Sorgo GR', 'Maní', 'Poroto', 'Caña de azúcar', 'Girasol-CV',
       'Papa', 'Arroz', 'Sin clasificar'
     ];
    
     // Filtrar los que realmente existen en nuestros datos
     var cultivosPrincipalesFiltrados = [];
     for (var k = 0; k < cultivosPrincipales.length; k++) {
       if (todosCultivos.indexOf(cultivosPrincipales[k]) !== -1) {
         cultivosPrincipalesFiltrados.push(cultivosPrincipales[k]);
       }
     }
    
     // Agregar cualquier otro cultivo que no esté en la lista principal
     for (var l = 0; l < todosCultivos.length; l++) {
       var cultivo = todosCultivos[l];
       if (cultivosPrincipalesFiltrados.indexOf(cultivo) === -1 &&
           !estaEnArray(cultivo, categoriasNoAgricolas) &&
           cultivo !== 'Sin clasificar') {
         cultivosPrincipalesFiltrados.push(cultivo);
       }
     }
    
     // Usar la lista filtrada
     cultivosPrincipales = cultivosPrincipalesFiltrados;
    
     // Calcular promedios por cultivo
     var promedios = {};
     for (var m = 0; m < cultivosPrincipales.length; m++) {
       var cultivoActual = cultivosPrincipales[m];
       var totalArea = 0;
       var totalPorcentaje = 0;
       var campanasConCultivo = 0;
      
       for (var n = 0; n < campanasArray.length; n++) {
         var campanaActual = campanasArray[n];
         if (campanas[campanaActual][cultivoActual]) {
           totalArea += campanas[campanaActual][cultivoActual].area || 0;
           totalPorcentaje += campanas[campanaActual][cultivoActual].porcentaje || 0;
           campanasConCultivo++;
         }
       }
      
       if (campanasConCultivo > 0) {
         promedios[cultivoActual] = {
           area: Math.round(totalArea / campanasConCultivo),
           porcentaje: Math.round(totalPorcentaje / campanasConCultivo)
         };
       } else {
         // Si no hay campañas, inicializamos con ceros
         promedios[cultivoActual] = {
           area: 0,
           porcentaje: 0
         };
       }
     }
    
     // Calcular promedios para las categorías principales
     var promedioAgricola = 0;
     var promedioNoAgricola = 0;
     var campanasValidas = 0;
    
     for (var o = 0; o < campanasArray.length; o++) {
       var campanaParaPromedio = campanasArray[o];
       if (campanas[campanaParaPromedio] &&
           campanas[campanaParaPromedio]['% Agrícola'] !== undefined &&
           campanas[campanaParaPromedio]['% No Agrícola'] !== undefined) {
         promedioAgricola += campanas[campanaParaPromedio]['% Agrícola'];
         promedioNoAgricola += campanas[campanaParaPromedio]['% No Agrícola'];
         campanasValidas++;
       }
     }
    
     promedioAgricola = campanasValidas > 0 ? Math.round(promedioAgricola / campanasValidas) : 0;
     promedioNoAgricola = campanasValidas > 0 ? Math.round(promedioNoAgricola / campanasValidas) : 0;
    
     // Crear panel para mostrar resultados
     var resultPanel = ui.Panel({
       style: {
         position: 'top-right',
         padding: '8px 15px',
         backgroundColor: 'white',
         border: '1px solid #ccc',
         width: '350px'
       }
     });
    
     var resultTitle = ui.Label({
       value: 'Análisis de Cultivos (2019-2024)',
       style: {
         fontWeight: 'bold',
         fontSize: '18px',
         margin: '0 0 10px 0'
       }
     });
     resultPanel.add(resultButton);
    
     // Añadir el panel de resultados al mapa
     Map.add(resultPanel);
    
     // También imprimir en la consola
     print('ANÁLISIS DE CULTIVOS (2019-2024)');
     print('Promedio Agrícola: ' + promedioAgricola + '%');
     print('Promedio No Agrícola: ' + promedioNoAgricola + '%');
     print('-----');
     print('Promedio por cultivo:');
    
     for (var s = 0; s < cultivosPrincipales.length; s++) {
       var cultivoConsola = cultivosPrincipales[s];
       if (promedios[cultivoConsola]) {
         var areaConsolaPromedio = promedios[cultivoConsola].area || 0;
         var porcentajeConsolaPromedio = promedios[cultivoConsola].porcentaje || 0;
        
         print(cultivoConsola + ': ' + porcentajeConsolaPromedio + '% (' +
               areaConsolaPromedio + ' ha)');
       }
     }
    
     // Exportar tabla a Drive
     var csvFeatures = [];
     for (var t = 0; t < cultivosPrincipales.length; t++) {
       var cultivoExport = cultivosPrincipales[t];
       if (promedios[cultivoExport]) {
         var properties = {
           'Cultivo': cultivoExport,
           'Promedio_Area_ha': promedios[cultivoExport].area || 0,
           'Promedio_Porcentaje': promedios[cultivoExport].porcentaje || 0
         };
        
         // Añadir datos para cada campaña
         for (var u = 0; u < campanasArray.length; u++) {
           var campanaExport = campanasArray[u];
           if (campanas[campanaExport][cultivoExport]) {
             properties[campanaExport + '_Area_ha'] = Math.round(campanas[campanaExport][cultivoExport].area) || 0;
             properties[campanaExport + '_Porcentaje'] = Math.round(campanas[campanaExport][cultivoExport].porcentaje) || 0;
           } else {
             properties[campanaExport + '_Area_ha'] = 0;
             properties[campanaExport + '_Porcentaje'] = 0;
           }
         }
        
         csvFeatures.push(ee.Feature(null, properties));
       }
     }
    
     var csvData = ee.FeatureCollection(csvFeatures);
     var exportName = 'Analisis_Cultivos_Promedio_' + Date.now();
    
     Export.table.toDrive({
       collection: csvData,
       description: exportName,
       fileFormat: 'CSV'
     });
    
     print('Se ha iniciado una exportación a Google Drive con nombre: ' + exportName);
   });
}


// Botón para calcular estadísticas detalladas
var detailedStatsButton = ui.Button({
 label: 'Calcular Promedio Detallado por Cultivo',
 onClick: function() {
   calcularEstadisticasDetalladas();
 }
});
panel.add(detailedStatsButton);


// Mensaje inicial
print('Seleccione una campaña del menú desplegable para visualizar los cultivos');
print('Área total del AOI (hectáreas):', areaTotalAOI);
"""

# Función para crear un botón que genere la visualización en GEE
def crear_boton_analisis_cultivos(poligonos):
    """
    Crea un botón para realizar análisis de cultivos en Google Earth Engine
    
    Args:
        poligonos: Lista de polígonos RENSPA
    """
    if not poligonos:
        st.warning("No hay polígonos disponibles para analizar. Primero consulte algún RENSPA con geometría.")
        return
    
    # Verificar si Earth Engine está inicializado
    ee_initialized = inicializar_earth_engine()
    
    if ee_initialized:
        if st.button("Analizar Cultivos Históricos (Earth Engine)", key="btn_analizar_cultivos"):
            with st.spinner("Preparando análisis de cultivos en Google Earth Engine..."):
                resultado = abrir_analisis_earth_engine(poligonos, CODIGO_EARTH_ENGINE_BASE)
                if resultado:
                    st.success("¡Análisis enviado! Se ha abierto una nueva pestaña con el análisis de cultivos históricos.")
                    st.info("Si no se abrió automáticamente, revise si su navegador bloqueó la ventana emergente.")
    else:
        st.warning("Para utilizar el análisis de cultivos, debe autenticar Google Earth Engine.")
Title);
    
     // Mostrar promedios de categorías principales
     resultPanel.add(ui.Label('Promedio en 5 campañas:', {fontWeight: 'bold'}));
     resultPanel.add(ui.Label('Agrícola: ' + promedioAgricola + '%',
       {margin: '5px 0 0 15px', fontWeight: 'bold', color: '#339820'}));
     resultPanel.add(ui.Label('No Agrícola: ' + promedioNoAgricola + '%',
       {margin: '0 0 15px 15px', fontWeight: 'bold', color: '#646b63'}));
    
     // Mostrar promedio por cultivo
     resultPanel.add(ui.Label('Promedio por cultivo:', {fontWeight: 'bold', margin: '10px 0 5px 0'}));
    
     // Crear una tabla para los promedios de cultivos
     var cultivosTable = ui.Panel({
       layout: ui.Panel.Layout.flow('vertical'),
       style: {
         margin: '0 0 0 15px'
       }
     });
    
     for (var p = 0; p < cultivosPrincipales.length; p++) {
       var cultivoTabla = cultivosPrincipales[p];
       if (promedios[cultivoTabla]) {
         var color = estaEnArray(cultivoTabla, categoriasNoAgricolas) ? '#646b63' : '#339820';
         if (cultivoTabla === 'Sin clasificar') color = '#b7b9bd';
        
         var areaPromedio = promedios[cultivoTabla].area || 0;
         var porcentajePromedio = promedios[cultivoTabla].porcentaje || 0;
        
         cultivosTable.add(ui.Label(
           cultivoTabla + ': ' + porcentajePromedio + '% (' +
           areaPromedio + ' ha)',
           {color: color, margin: '2px 0'}
         ));
       }
     }
    
     resultPanel.add(cultivosTable);
    
     // Crear botón para ver detalle por campaña
     var detailButton = ui.Button({
       label: 'Ver detalle por campaña',
       onClick: function() {
         // Crear panel para los detalles
         var detailPanel = ui.Panel({
           style: {
             position: 'bottom-right',
             padding: '8px 15px',
             backgroundColor: 'white',
             border: '1px solid #ccc',
             width: '350px'
           }
         });
        
         var detailTitle = ui.Label({
           value: 'Detalle por Campaña',
           style: {
             fontWeight: 'bold',
             fontSize: '18px',
             margin: '0 0 10px 0'
           }
         });
         detailPanel.add(detailTitle);
        
         // Mostrar datos por campaña
         for (var q = 0; q < campanasArray.length; q++) {
           var campanaDetalle = campanasArray[q];
           var campanaObj = campanas[campanaDetalle];
          
           detailPanel.add(ui.Label('Campaña ' + campanaDetalle + ':',
             {margin: '10px 0 0 0', fontWeight: 'bold'}));
          
           var porcentajeAgricola = campanaObj['% Agrícola'] || 0;
           var porcentajeNoAgricola = campanaObj['% No Agrícola'] || 0;
          
           detailPanel.add(ui.Label('Agrícola: ' + porcentajeAgricola + '%',
             {margin: '0 0 0 15px', color: '#339820'}));
          
           detailPanel.add(ui.Label('No Agrícola: ' + porcentajeNoAgricola + '%',
             {margin: '0 0 5px 15px', color: '#646b63'}));
          
           // Panel para cultivos específicos
           var campanaDetails = ui.Panel({
             layout: ui.Panel.Layout.flow('vertical'),
             style: {
               margin: '0 0 0 15px'
             }
           });
          
           for (var r = 0; r < cultivosPrincipales.length; r++) {
             var cultivoDetalle = cultivosPrincipales[r];
             if (campanaObj[cultivoDetalle]) {
               var colorDetalle = estaEnArray(cultivoDetalle, categoriasNoAgricolas) ? '#646b63' : '#339820';
               if (cultivoDetalle === 'Sin clasificar') colorDetalle = '#b7b9bd';
              
               var areaCultivo = Math.round(campanaObj[cultivoDetalle].area) || 0;
               var porcentajeCultivo = Math.round(campanaObj[cultivoDetalle].porcentaje) || 0;
              
               campanaDetails.add(ui.Label(
                 cultivoDetalle + ': ' + porcentajeCultivo + '% (' +
                 areaCultivo + ' ha)',
                 {color: colorDetalle, margin: '2px 0'}
               ));
             }
           }
          
           detailPanel.add(campanaDetails);
         }
        
         Map.add(detailPanel);
       }
     });
    
     result
# Verificar si Earth Engine está disponible y mostrar información
if ee_disponible:
    # Crear una sección en la barra lateral con información sobre Earth Engine
    from earth_engine_integration import mostrar_info_earth_engine_sidebar
    mostrar_info_earth_engine_sidebar()
else:
    # Mostrar advertencia si Earth Engine no está disponible
    st.sidebar.markdown("---")
    st.sidebar.subheader("Google Earth Engine")
    st.sidebar.warning("Google Earth Engine no está disponible")
    st.sidebar.info(
        "Para habilitar el análisis de cultivos históricos, instala las siguientes dependencias:\n"
        "```\npip install earthengine-api geemap\n```"
    )

# Información en el pie de página
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado para análisis agrícola en Argentina")
