import streamlit as st
import ee
import geemap

def inicializar_earth_engine():
    """Inicializa la API de Earth Engine si no está ya inicializada"""
    try:
        ee.Initialize()
        return True
    except Exception as e:
        st.error(f"Error al inicializar Earth Engine: {str(e)}")
        return False

def crear_boton_analisis_cultivos(poligonos):
    """
    Crea un botón para analizar cultivos históricos usando Google Earth Engine
    
    Args:
        poligonos: Lista de diccionarios con información de polígonos
    """
    if st.button("Analizar Cultivos Históricos"):
        with st.spinner("Analizando cultivos con Google Earth Engine..."):
            # Inicializar Earth Engine
            if not inicializar_earth_engine():
                st.error("No se pudo inicializar Google Earth Engine")
                return
            
            # Crear un mapa de Earth Engine
            m = geemap.Map()
            
            # Procesar cada polígono
            for i, pol in enumerate(poligonos):
                if 'coords' in pol:
                    # Convertir coordenadas de [lon, lat] a [lat, lon] para EE
                    ee_coords = [[coord[1], coord[0]] for coord in pol['coords']]
                    
                    # Crear polígono para Earth Engine
                    polygon = ee.Geometry.Polygon([ee_coords])
                    
                    # Añadir polígono al mapa
                    m.add_layer(ee.Feature(polygon), {'color': 'red'}, f"Polígono {i+1}")
            
            # Mostrar el mapa
            m.to_streamlit(height=600)

def mostrar_info_earth_engine_sidebar():
    """Muestra información sobre Earth Engine en la barra lateral"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Google Earth Engine")
    
    # Verificar si Earth Engine está disponible
    try:
        ee.Initialize()
        estado = "disponible"
    except:
        estado = "no inicializado"
    
    st.sidebar.info(f"""
    Google Earth Engine está {estado}.
    
    Esta herramienta permite analizar los cultivos históricos (2019-2023) 
    en los campos utilizando datos satelitales de alta resolución.
    """)
