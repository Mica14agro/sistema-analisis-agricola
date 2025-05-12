import streamlit as st
import folium
from streamlit_folium import folium_static

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
    
    if st.button("Procesar"):
        # Aquí iría la lógica real
        st.success(f"Procesando CUIT: {cuit}")
        st.info("Versión de demostración - La funcionalidad completa estará disponible próximamente")
        
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

# Información en el pie de página
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado para análisis agrícola en Argentina")
