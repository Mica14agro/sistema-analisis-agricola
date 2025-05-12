import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import random

# Intentar importar folium y streamlit_folium
try:
    import folium
    from streamlit_folium import folium_static
    folium_disponible = True
except ImportError:
    folium_disponible = False

# Intentar importar matplotlib
try:
    import matplotlib.pyplot as plt
    matplotlib_disponible = True
except ImportError:
    matplotlib_disponible = False

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Análisis Agrícola",
    page_icon="🌱",
    layout="wide"
)

# Título principal
st.title("Sistema de Análisis Agrícola - RENSPA")

# Introducción
st.markdown("""
Este sistema automatiza el análisis de datos agrícolas en Argentina:
1. Obtiene información de RENSPA desde SENASA
2. Visualiza campos en mapas interactivos
3. Prepara datos para Google Earth Engine
""")

# Menú de navegación
st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Seleccione una función:",
    ["Inicio", "Procesar por CUIT", "Procesar lista de RENSPA", "Convertir CSV a GeoJSON", "Datos históricos", "Mapa de ejemplo"]
)

# Contenido según la opción seleccionada
if opcion == "Inicio":
    st.header("Bienvenido al Sistema de Análisis Agrícola")
    
    # Descripción principal
    st.markdown("""
    Esta aplicación está diseñada para ayudar a los productores agrícolas y profesionales del sector a:
    
    * **Obtener datos RENSPA** directamente desde SENASA
    * **Visualizar campos** en mapas interactivos
    * **Analizar distribución** de cultivos y áreas
    * **Generar archivos GeoJSON** para sistemas de información geográfica
    * **Preparar código** para Google Earth Engine
    """)
    
    # Mostrar instrucciones básicas
    st.subheader("Instrucciones de uso")
    
    tab1, tab2, tab3, tab4 = st.tabs(["CUIT", "Lista RENSPA", "CSV a GeoJSON", "Datos históricos"])
    
    with tab1:
        st.markdown("""
        1. Seleccione "Procesar por CUIT" en el menú de navegación
        2. Ingrese un número de CUIT válido
        3. Especifique si desea procesar solo RENSPA activos
        4. Haga clic en "Procesar" para obtener los datos
        5. Visualice los resultados y descargue los archivos generados
        """)
    
    with tab2:
        st.markdown("""
        1. Seleccione "Procesar lista de RENSPA" en el menú de navegación
        2. Ingrese los números de RENSPA manualmente o cargue un archivo
        3. Haga clic en "Procesar RENSPA" para obtener los datos
        4. Visualice los resultados y descargue los archivos generados
        """)
    
    with tab3:
        st.markdown("""
        1. Seleccione "Convertir CSV a GeoJSON" en el menú de navegación
        2. Cargue un archivo CSV con datos de RENSPA y polígonos
        3. Verifique la vista previa y la estructura de los datos
        4. Descargue el archivo GeoJSON generado
        5. Utilice el código proporcionado para visualizar en Google Earth Engine
        """)
    
    with tab4:
        st.markdown("""
        1. Seleccione "Datos históricos" en el menú de navegación
        2. Elija un campo y una campaña agrícola
        3. Explore los datos y visualizaciones disponibles
        4. Descargue los datos históricos para análisis adicionales
        """)
    
    # Información adicional
    st.subheader("Sobre esta aplicación")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Esta herramienta ha sido desarrollada para automatizar el proceso de análisis agrícola en Argentina,
        facilitando el acceso y visualización de datos RENSPA (Registro Nacional Sanitario de Productores Agropecuarios).
        
        **Características principales:**
        
        * Interfaz intuitiva y fácil de usar
        * Visualización geoespacial interactiva
        * Generación de archivos en formatos estándar
        * Compatibilidad con Google Earth Engine
        """)
    
    with col2:
        # Mostrar imagen o logo si se tiene
        st.info("Versión de demostración 1.0")
        st.warning("Los datos mostrados son simulados con fines ilustrativos.")
    
elif opcion == "Procesar por CUIT":
    st.header("Procesar por CUIT")
    
    # Formulario para ingresar CUIT
    cuit = st.text_input("Ingrese el CUIT (formato: XX-XXXXXXXX-X):", "30-65425756-2")
    
    # Opciones de procesamiento
    col1, col2 = st.columns(2)
    with col1:
        solo_activos = st.checkbox("Solo RENSPA activos", value=True)
    with col2:
        buffer_distancia = st.slider("Distancia buffer para agrupar campos (m)", 0, 100, 5)
    
    if st.button("Procesar"):
        # Mostrar un indicador de procesamiento
        with st.spinner('Procesando CUIT...'):
            # Simulación de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simular la obtención de datos (paso 1)
            status_text.text("Consultando API de SENASA...")
            progress_bar.progress(20)
            time.sleep(1)  # Simular procesamiento
            
            # Datos simulados de RENSPA
            renspa_simulados = [
                {"renspa": "01.001.0.00123/01", "titular": "AGRICULTOR EJEMPLO 1", "localidad": "Tandil", "activo": True},
                {"renspa": "01.001.0.00456/02", "titular": "AGRICULTOR EJEMPLO 2", "localidad": "Olavarría", "activo": True},
                {"renspa": "01.001.0.00789/03", "titular": "AGRICULTOR EJEMPLO 3", "localidad": "Azul", "activo": False},
                {"renspa": "01.001.0.01012/04", "titular": "AGRICULTOR EJEMPLO 4", "localidad": "Balcarce", "activo": True}
            ]
            
            # Filtrar por activos si se solicita
            if solo_activos:
                renspa_filtrados = [r for r in renspa_simulados if r["activo"]]
                st.success(f"Se encontraron {len(renspa_filtrados)} RENSPA activos de un total de {len(renspa_simulados)}")
            else:
                renspa_filtrados = renspa_simulados
                st.success(f"Se encontraron {len(renspa_simulados)} RENSPA en total")
            
            # Actualizar progreso
            status_text.text("Procesando polígonos...")
            progress_bar.progress(60)
            time.sleep(1)  # Simular procesamiento
            
            # Mostrar los datos en una tabla
            df = pd.DataFrame(renspa_filtrados)
            st.subheader("RENSPA encontrados:")
            st.dataframe(df)
            
            # Completar progreso
            status_text.text("Procesamiento completo!")
            progress_bar.progress(100)
            
            # Mostrar botones de descarga simulada
            st.subheader("Descargar resultados:")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Descargar datos CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=f'renspa_{cuit.replace("-", "")}.csv',
                    mime='text/csv',
                )
            with col2:
                st.download_button(
                    label="Descargar GeoJSON (simulado)",
                    data="{}",  # Datos simulados
                    file_name=f'renspa_{cuit.replace("-", "")}.geojson',
                    mime='application/json',
                )
            
            # Mostrar mapa con polígonos simulados
            if folium_disponible:
                st.subheader("Visualización de campos:")
                
                # Crear mapa base
                m = folium.Map(location=[-37.33, -59.13], zoom_start=8)
                
                # Añadir polígonos simulados para cada RENSPA
                for i, renspa in enumerate(renspa_filtrados):
                    # Crear un polígono aleatorio alrededor de un punto central
                    
                    # Coordenadas base según localidad
                    if renspa["localidad"] == "Tandil":
                        centro = [-37.33, -59.13]
                    elif renspa["localidad"] == "Olavarría":
                        centro = [-36.89, -60.32]
                    elif renspa["localidad"] == "Azul":
                        centro = [-36.77, -59.85]
                    elif renspa["localidad"] == "Balcarce":
                        centro = [-37.84, -58.25]
                    else:
                        centro = [-37.33 + random.uniform(-0.5, 0.5), -59.13 + random.uniform(-0.5, 0.5)]
                    
                    # Crear vértices para un polígono aleatorio
                    vertices = []
                    for j in range(5):  # Polígono de 5 lados
                        # Generar un punto aleatorio cerca del centro
                        lat = centro[0] + random.uniform(-0.05, 0.05)
                        lon = centro[1] + random.uniform(-0.05, 0.05)
                        vertices.append([lat, lon])
                    
                    # Cerrar el polígono
                    vertices.append(vertices[0])
                    
                    # Color según estado
                    color = 'green' if renspa["activo"] else 'orange'
                    
                    # Añadir polígono al mapa
                    folium.Polygon(
                        locations=vertices,
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.3,
                        tooltip=f"RENSPA: {renspa['renspa']}",
                        popup=f"<b>RENSPA:</b> {renspa['renspa']}<br><b>Titular:</b> {renspa['titular']}<br><b>Localidad:</b> {renspa['localidad']}"
                    ).add_to(m)
                
                # Añadir marcadores para ciudades de referencia
                ciudades = [
                    ["Tandil", -37.33, -59.13],
                    ["Olavarría", -36.89, -60.32],
                    ["Azul", -36.77, -59.85],
                    ["Balcarce", -37.84, -58.25]
                ]
                
                for ciudad, lat, lon in ciudades:
                    folium.Marker(
                        [lat, lon],
                        tooltip=ciudad,
                        icon=folium.Icon(color="blue", icon="info-sign")
                    ).add_to(m)
                
                # Mostrar el mapa
                folium_static(m)
                
                # Código JavaScript simulado para Google Earth Engine
                st.subheader("Código para Google Earth Engine:")
                code = """// Código para Google Earth Engine (simulado)
var poligonos = [];
// Polígono para RENSPA: 01.001.0.00123/01
var coords_01_001_0_00123_01 = [
  [-37.33, -59.13],
  [-37.35, -59.15],
  [-37.32, -59.18],
  [-37.30, -59.12],
  [-37.33, -59.13]
];
var poligono_01_001_0_00123_01 = ee.Geometry.Polygon([coords_01_001_0_00123_01]);
var feature_01_001_0_00123_01 = ee.Feature(poligono_01_001_0_00123_01, {
  "renspa": "01.001.0.00123/01",
  "titular": "AGRICULTOR EJEMPLO 1",
  "localidad": "Tandil",
  "sistema": "RENSPA-SENASA"
});
poligonos.push(feature_01_001_0_00123_01);

// Crear feature collection con todos los polígonos
var featureCollection = ee.FeatureCollection(poligonos);

// Centrar el mapa en los polígonos
Map.centerObject(featureCollection);

// Mostrar los polígonos en el mapa
Map.addLayer(featureCollection, {color: "red", fillColor: "red66", width: 2}, "RENSPA Polígonos");
"""
                st.code(code, language="javascript")
            else:
                st.warning("Para visualizar mapas, instala folium y streamlit-folium con: pip install folium streamlit-folium")
        
elif opcion == "Procesar lista de RENSPA":
    st.header("Procesar lista de RENSPA")
    
    # Opciones de entrada
    input_type = st.radio(
        "Seleccione método de entrada:",
        ["Ingresar manualmente", "Cargar archivo"]
    )
    
    renspa_list = []
    
    if input_type == "Ingresar manualmente":
        # Área de texto para ingresar múltiples RENSPA
        renspa_input = st.text_area(
            "Ingrese los RENSPA (uno por línea):", 
            "01.001.0.00123/01\n01.001.0.00456/02\n01.001.0.00789/03",
            height=150
        )
        
        if renspa_input:
            renspa_list = [line.strip() for line in renspa_input.split('\n') if line.strip()]
    else:
        uploaded_file = st.file_uploader("Suba un archivo TXT con un RENSPA por línea", type=['txt'])
        
        if uploaded_file:
            content = uploaded_file.getvalue().decode('utf-8')
            renspa_list = [line.strip() for line in content.split('\n') if line.strip()]
            st.success(f"Archivo cargado con {len(renspa_list)} RENSPA")
    
    # Mostrar lista de RENSPA a procesar
    if renspa_list:
        st.write(f"RENSPA a procesar ({len(renspa_list)}):")
        st.write(", ".join(renspa_list[:10]) + ("..." if len(renspa_list) > 10 else ""))
    
    # Botón para procesar
    if st.button("Procesar RENSPA") and renspa_list:
        # Mostrar un indicador de procesamiento
        with st.spinner('Procesando RENSPA...'):
            # Simulación de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simular la obtención de datos
            status_text.text("Consultando API de SENASA...")
            progress_bar.progress(20)
            time.sleep(1)  # Simular procesamiento
            
            # Datos simulados para cada RENSPA
            renspa_procesados = []
            for i, renspa in enumerate(renspa_list):
                # Datos simulados
                datos = {
                    "renspa": renspa,
                    "titular": f"TITULAR EJEMPLO {i+1}",
                    "localidad": ["Tandil", "Olavarría", "Azul", "Balcarce"][i % 4],
                    "superficie": round(50 + i * 10, 2)
                }
                renspa_procesados.append(datos)
                
                # Actualizar progreso
                progress_bar.progress(20 + (i+1) * 60 // len(renspa_list))
            
            # Mostrar los datos en una tabla
            status_text.text("Generando resultados...")
            df = pd.DataFrame(renspa_procesados)
            st.subheader("RENSPA procesados:")
            st.dataframe(df)
            
            # Completar progreso
            status_text.text("Procesamiento completo!")
            progress_bar.progress(100)
            
            # Mostrar mapa con polígonos simulados para los RENSPA
            if folium_disponible:
                st.subheader("Visualización de campos:")
                
                # Crear mapa base
                m = folium.Map(location=[-37.33, -59.13], zoom_start=8)
                
                # Añadir polígonos simulados para cada RENSPA
                ciudades_coords = {
                    "Tandil": [-37.33, -59.13],
                    "Olavarría": [-36.89, -60.32],
                    "Azul": [-36.77, -59.85],
                    "Balcarce": [-37.84, -58.25]
                }
                
                for renspa_data in renspa_procesados:
                    # Coordenadas base según localidad
                    centro = ciudades_coords.get(
                        renspa_data["localidad"], 
                        [-37.33 + random.uniform(-0.5, 0.5), -59.13 + random.uniform(-0.5, 0.5)]
                    )
                    
                    # Crear vértices para un polígono aleatorio
                    vertices = []
                    for j in range(5):  # Polígono de 5 lados
                        # Generar un punto aleatorio cerca del centro
                        lat = centro[0] + random.uniform(-0.05, 0.05)
                        lon = centro[1] + random.uniform(-0.05, 0.05)
                        vertices.append([lat, lon])
                    
                    # Cerrar el polígono
                    vertices.append(vertices[0])
                    
                    # Añadir polígono al mapa
                    folium.Polygon(
                        locations=vertices,
                        color='green',
                        fill=True,
                        fill_color='green',
                        fill_opacity=0.3,
                        tooltip=f"RENSPA: {renspa_data['renspa']}",
                        popup=f"<b>RENSPA:</b> {renspa_data['renspa']}<br><b>Titular:</b> {renspa_data['titular']}<br><b>Localidad:</b> {renspa_data['localidad']}<br><b>Superficie:</b> {renspa_data['superficie']} ha"
                    ).add_to(m)
                
                # Añadir marcadores para ciudades de referencia
                for ciudad, coords in ciudades_coords.items():
                    folium.Marker(
                        coords,
                        tooltip=ciudad,
                        icon=folium.Icon(color="blue", icon="info-sign")
                    ).add_to(m)
                
                # Mostrar el mapa
                folium_static(m)
            else:
                st.warning("Para visualizar mapas, instala folium y streamlit-folium")
            
            # Opciones de descarga
            st.subheader("Descargar resultados:")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Descargar datos CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name='renspa_procesados.csv',
                    mime='text/csv',
                )
            with col2:
                st.download_button(
                    label="Descargar GeoJSON (simulado)",
                    data="{}",  # Datos simulados
                    file_name='renspa_procesados.geojson',
                    mime='application/json',
                )
    
elif opcion == "Convertir CSV a GeoJSON":
    st.header("Convertir CSV a GeoJSON")
    
    st.write("Esta herramienta convierte archivos CSV con datos de RENSPA a formato GeoJSON para uso en sistemas GIS.")
    
    # Mostrar ejemplo del formato esperado
    with st.expander("Ver formato esperado del CSV"):
        st.markdown("""
        El archivo CSV debe contener al menos estas columnas:
        - `renspa`: Número de RENSPA (ejemplo: 01.001.0.00123/01)
        - `poligono`: String con el formato de polígono de SENASA (ejemplo: "(lat1,lon1)(lat2,lon2)...")
        
        Columnas opcionales pero recomendadas:
        - `titular`: Nombre del titular
        - `localidad`: Localidad del establecimiento
        - `superficie`: Superficie en hectáreas
        
        **Ejemplo de CSV:**
        """)
        
        ejemplo_csv = """renspa,titular,localidad,poligono,superficie
01.001.0.00123/01,AGRICULTOR EJEMPLO 1,Tandil,"(-37.33,-59.13)(-37.35,-59.15)(-37.32,-59.18)(-37.30,-59.12)",120.5
01.001.0.00456/02,AGRICULTOR EJEMPLO 2,Olavarría,"(-36.89,-60.32)(-36.91,-60.34)(-36.87,-60.36)(-36.85,-60.30)",85.3"""
        
        st.code(ejemplo_csv)
    
    # Subir archivo CSV
    uploaded_file = st.file_uploader("Suba un archivo CSV con datos de RENSPA", type=['csv'])
    
    if uploaded_file:
        # Mostrar un indicador de procesamiento
        with st.spinner('Procesando archivo CSV...'):
            try:
                # Leer el CSV
                df = pd.read_csv(uploaded_file)
                st.success(f"Archivo cargado correctamente: {uploaded_file.name}")
                
                # Verificar columnas requeridas
                columnas_requeridas = ['renspa', 'poligono']
                columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
                
                if columnas_faltantes:
                    st.error(f"El archivo no contiene las columnas requeridas: {', '.join(columnas_faltantes)}")
                    st.stop()
                
                # Mostrar un resumen de los datos
                st.subheader("Resumen de datos")
                st.write(f"Total de registros: {len(df)}")
                st.write(f"Columnas disponibles: {', '.join(df.columns)}")
                
                # Mostrar una muestra de los datos
                st.subheader("Muestra de datos")
                st.dataframe(df.head())
                
                # Simular la conversión a GeoJSON
                st.subheader("Proceso de conversión")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Extrayendo coordenadas...")
                progress_bar.progress(30)
                time.sleep(1)  # Simular procesamiento
                
                status_text.text("Generando geometrías GeoJSON...")
                progress_bar.progress(60)
                time.sleep(1)  # Simular procesamiento
                
                status_text.text("Finalizando el proceso...")
                progress_bar.progress(100)
                
                # Generar GeoJSON simulado
                geojson_data = {
                    "type": "FeatureCollection",
                    "features": []
                }
                
                for i, row in df.head().iterrows():
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "renspa": row['renspa']
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-59.13, -37.33], [-59.15, -37.35], [-59.18, -37.32], [-59.12, -37.30], [-59.13, -37.33]]]
                        }
                    }
                    
                    # Añadir propiedades adicionales si existen
                    for col in ['titular', 'localidad', 'superficie']:
                        if col in df.columns:
                            feature["properties"][col] = str(row[col])
                    
                    geojson_data["features"].append(feature)
                
                # Convertir a string
                geojson_str = json.dumps(geojson_data, indent=2)
                
                # Mostrar GeoJSON de muestra
                st.subheader("Vista previa del GeoJSON generado")
                st.code(geojson_str[:500] + "...", language="json")
                
                # Opciones de descarga
                st.subheader("Descargar resultados")
                
                st.download_button(
                    label="Descargar GeoJSON",
                    data=geojson_str,
                    file_name=f"{uploaded_file.name.split('.')[0]}.geojson",
                    mime="application/json",
                )
                
                # Añadir código para Google Earth Engine
                st.subheader("Código para Google Earth Engine")
                gee_code = f"""// Código para usar el GeoJSON en Google Earth Engine
// Primero, sube el archivo GeoJSON como un Asset en Earth Engine

// Luego usa este código para visualizarlo
var renspa = ee.FeatureCollection("users/TU_USUARIO/{uploaded_file.name.split('.')[0]}");

// Visualizar en el mapa
Map.centerObject(renspa);
Map.addLayer(renspa, {{color: 'green'}}, "RENSPA - {uploaded_file.name.split('.')[0]}");

// Calcular área total
var areaTotal = renspa.geometry().area().divide(10000); // Convertir a hectáreas
print("Área total en hectáreas:", areaTotal);
"""
                st.code(gee_code, language="javascript")
                
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")

elif opcion == "Datos históricos":
    st.header("Datos Históricos de Campos Agrícolas")
    
    # Selector de campo
    campo_seleccionado = st.selectbox(
        "Seleccione un campo:",
        ["Campo 1 - Tandil", "Campo 2 - Olavarría", "Campo 3 - Azul"]
    )
    
    # Selector de año
    año_seleccionado = st.select_slider(
        "Seleccione campaña agrícola:",
        options=["2018/19", "2019/20", "2020/21", "2021/22", "2022/23", "2023/24"]
    )
    
    # Mostrar información del campo
    st.subheader(f"Información de {campo_seleccionado} - Campaña {año_seleccionado}")
    
    # Datos simulados según el campo y año seleccionados
    if campo_seleccionado == "Campo 1 - Tandil":
        area_total = 150
        datos_cultivos = {
            "2018/19": {"Soja": 70, "Maíz": 50, "Trigo": 20, "Sin cultivo": 10},
            "2019/20": {"Soja": 80, "Maíz": 40, "Trigo": 20, "Sin cultivo": 10},
            "2020/21": {"Soja": 60, "Maíz": 60, "Trigo": 20, "Sin cultivo": 10},
            "2021/22": {"Soja": 50, "Maíz": 70, "Trigo": 20, "Sin cultivo": 10},
            "2022/23": {"Soja": 65, "Maíz": 55, "Trigo": 20, "Sin cultivo": 10},
            "2023/24": {"Soja": 60, "Maíz": 60, "Trigo": 20, "Sin cultivo": 10},
        }
        ubicacion = [-37.33, -59.13]  # Tandil
    elif campo_seleccionado == "Campo 2 - Olavarría":
        area_total = 200
        datos_cultivos = {
            "2018/19": {"Soja": 100, "Maíz": 60, "Trigo": 30, "Sin cultivo": 10},
            "2019/20": {"Soja": 90, "Maíz": 70, "Trigo": 30, "Sin cultivo": 10},
            "2020/21": {"Soja": 80, "Maíz": 80, "Trigo": 30, "Sin cultivo": 10},
            "2021/22": {"Soja": 70, "Maíz": 90, "Trigo": 30, "Sin cultivo": 10},
            "2022/23": {"Soja": 85, "Maíz": 75, "Trigo": 30, "Sin cultivo": 10},
            "2023/24": {"Soja": 80, "Maíz": 80, "Trigo": 30, "Sin cultivo": 10},
        }
        ubicacion = [-36.89, -60.32]  # Olavarría
    else:  # Campo 3 - Azul
        area_total = 180
        datos_cultivos = {
            "2018/19": {"Soja": 80, "Maíz": 60, "Trigo": 25, "Sin cultivo": 15},
            "2019/20": {"Soja": 70, "Maíz": 70, "Trigo": 25, "Sin cultivo": 15},
            "2020/21": {"Soja": 60, "Maíz": 80, "Trigo": 25, "Sin cultivo": 15},
            "2021/22": {"Soja": 75, "Maíz": 65, "Trigo": 25, "Sin cultivo": 15},
            "2022/23": {"Soja": 70, "Maíz": 70, "Trigo": 25, "Sin cultivo": 15},
            "2023/24": {"Soja": 65, "Maíz": 75, "Trigo": 25, "Sin cultivo": 15},
        }
        ubicacion = [-36.77, -59.85]  # Azul
    
    # Datos para el año seleccionado
    datos_año = datos_cultivos[año_seleccionado]
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Área Total", f"{area_total} ha")
    with col2:
        st.metric("Soja", f"{datos_año['Soja']} ha")
    with col3:
        st.metric("Maíz", f"{datos_año['Maíz']} ha")
    with col4:
        st.metric("Trigo", f"{datos_año['Trigo']} ha")
    
    # Mostrar gráfico de distribución de cultivos
    st.subheader("Distribución de cultivos")
    
    if matplotlib_disponible:
        # Gráfico de torta
        fig, ax = plt.subplots(figsize=(8, 6))
        cultivos = list(datos_año.keys())
        valores = list(datos_año.values())
        colores = ['#4CAF50', '#FFC107', '#2196F3', '#9E9E9E']
        
        ax.pie(valores, labels=cultivos, autopct='%1.1f%%', startangle=90, colors=colores)
        ax.axis('equal')  # Aspecto igual para asegurar que el gráfico sea circular
        
        st.pyplot(fig)
    else:
        st.warning("Para visualizar gráficos, instala matplotlib: pip install matplotlib")
    
    # Mostrar mapa del campo si folium está disponible
    st.subheader("Ubicación del campo")
    
    if folium_disponible:
        # Crear mapa
        m = folium.Map(location=ubicacion, zoom_start=12)
        
        # Generar polígono simulado para el campo
        vertices = []
        for i in range(6):  # Polígono de 6 lados
            lat = ubicacion[0] + random.uniform(-0.07, 0.07)
            lon = ubicacion[1] + random.uniform(-0.07, 0.07)
            vertices.append([lat, lon])
        
        vertices.append(vertices[0])  # Cerrar el polígono
        
        # Añadir polígono al mapa
        folium.Polygon(
            locations=vertices,
            color='green',
            fill=True,
            fill_color='green',
            fill_opacity=0.3,
            tooltip=campo_seleccionado,
            popup=f"<b>Campo:</b> {campo_seleccionado}<br><b>Área:</b> {area_total} ha"
        ).add_to(m)
        
        # Añadir marcador para la ciudad
        ciudad = campo_seleccionado.split(" - ")[1]
        folium.Marker(
            ubicacion,
            tooltip=ciudad,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)
        
        # Mostrar el mapa
        folium_static(m)
    else:
        st.warning("Para visualizar mapas, instala folium y streamlit-folium")
    
    # Datos históricos en tabla
    st.subheader("Datos históricos por campaña")
    
    # Crear DataFrame para todas las campañas
    datos_historicos = []
    for año, datos in datos_cultivos.items():
        fila = {"Campaña": año}
        fila.update(datos)
        datos_historicos.append(fila)
    
    df_historico = pd.DataFrame(datos_historicos)
    st.dataframe(df_historico, use_container_width=True)
    
    # Opción para descargar
    st.download_button(
        label="Descargar datos históricos",
        data=df_historico.to_csv(index=False).encode('utf-8'),
        file_name=f"historico_{campo_seleccionado.replace(' - ', '_').replace(' ', '_')}.csv",
        mime='text/csv',
    )

elif opcion == "Mapa de ejemplo":
    st.header("Mapa de Ejemplo")
    
    if folium_disponible:
        # Crear un mapa centrado en Argentina
        m = folium.Map(location=[-34.603722, -58.381592], zoom_start=5)
        
        # Añadir algunos marcadores de ejemplo
        folium.Marker(
            [-34.603722, -58.381592], 
            popup="Buenos Aires",
            tooltip="Capital Federal"
        ).add_to(m)
        
        folium.Marker(
            [-32.8894587, -68.8458386], 
            popup="Mendoza",
            tooltip="Mendoza"
        ).add_to(m)
        
        # Añadir un polígono de ejemplo
        folium.Polygon(
            locations=[
                [-37.33, -59.13],  # Tandil
                [-36.89, -60.32],  # Olavarría
                [-36.77, -59.85],  # Azul
            ],
            color='green',
            fill=True,
            fill_color='green',
            fill_opacity=0.2,
            popup="Región de ejemplo"
        ).add_to(m)
        
        # Mostrar el mapa en la aplicación
        folium_static(m)
    else:
        st.warning("Para visualizar mapas, instala folium y streamlit-folium con: pip install folium streamlit-folium")

# Información en el pie de página
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado para análisis agrícola en Argentina")
