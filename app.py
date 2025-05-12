import streamlit as st
import pandas as pd
import numpy as np

# Intentar importar folium y streamlit_folium
try:
    import folium
    from streamlit_folium import folium_static
    folium_disponible = True
except ImportError:
    folium_disponible = False

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
    ["Inicio", "Procesar por CUIT", "Procesar lista de RENSPA", "Convertir CSV a GeoJSON", "Mapa de ejemplo"]
)

# Contenido según la opción seleccionada
if opcion == "Inicio":
    st.header("Bienvenido")
    st.write("Seleccione una opción en el menú de navegación para comenzar.")
    
    # Mostrar algunas imágenes o información adicional
    st.info("Esta es una versión inicial de la aplicación.")
    
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
            import time
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
            
            # Mostrar mapa si folium está disponible
            if folium_disponible:
                st.subheader("Visualización de campos:")
                
                # Crear mapa base
                m = folium.Map(location=[-37.33, -59.13], zoom_start=8)
                
                # Añadir polígonos simulados para cada RENSPA
                for i, renspa in enumerate(renspa_filtrados):
                    # Crear un polígono aleatorio alrededor de un punto central
                    import random
                    
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
            else:
                st.warning("Para visualizar mapas, instala folium y streamlit-folium con: pip install folium streamlit-folium")
        
elif opcion == "Procesar lista de RENSPA":
    st.header("Procesar lista de RENSPA")
    
    # Área de texto para ingresar múltiples RENSPA
    renspa_input = st.text_area("Ingrese los RENSPA (uno por línea):", height=150)
    
    if st.button("Procesar RENSPA"):
        renspa_list = [line.strip() for line in renspa_input.split('\n') if line.strip()]
        st.success(f"Se procesarán {len(renspa_list)} RENSPA")
        st.info("Versión de demostración - La funcionalidad completa estará disponible próximamente")
    
elif opcion == "Convertir CSV a GeoJSON":
    st.header("Convertir CSV a GeoJSON")
    
    # Subir archivo CSV
    uploaded_file = st.file_uploader("Suba un archivo CSV con datos de RENSPA", type=['csv'])
    
    if uploaded_file is not None:
        st.success(f"Archivo cargado: {uploaded_file.name}")
        st.info("Versión de demostración - La funcionalidad completa estará disponible próximamente")

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
