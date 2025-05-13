# Aplicación de Consulta RENSPA con Google Earth Engine

Esta aplicación permite consultar y visualizar información agrícola de SENASA, incluyendo análisis histórico de cultivos utilizando Google Earth Engine.

## Características

- Consulta de RENSPA por CUIT individual
- Consulta por lista de RENSPA
- Consulta por múltiples CUITs con diferenciación por colores
- Visualización de polígonos en mapas interactivos
- Descarga de datos en formatos KMZ, GeoJSON y CSV
- **Análisis de cultivos históricos** con Google Earth Engine

## Requisitos

```
streamlit==1.29.0
pandas==2.1.3
numpy==1.26.2
folium==0.14.0
streamlit-folium==0.15.0
requests==2.31.0
earthengine-api
geemap
```

## Instalación

1. Clona este repositorio o descarga los archivos

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Para utilizar Google Earth Engine, necesitas tener una cuenta activa:
   - Regístrate en [Google Earth Engine](https://earthengine.google.com/)
   - Instala la autenticación:
     ```bash
     earthengine authenticate
     ```

## Estructura de archivos

- `app.py`: Aplicación principal de Streamlit
- `earth_engine_integration.py`: Módulo para la integración con Google Earth Engine

## Uso

1. Inicia la aplicación:

```bash
streamlit run app.py
```

2. Usa la interfaz para:
   - Consultar RENSPA por CUIT
   - Visualizar polígonos en mapas interactivos
   - Analizar histórico de cultivos con Google Earth Engine
   - Descargar datos en varios formatos

## Flujo de trabajo para análisis de cultivos

1. Consulta RENSPA por CUIT o lista de RENSPA
2. Visualiza los polígonos en el mapa
3. Haz clic en el botón "Analizar Cultivos Históricos"
4. Se abrirá una nueva ventana con el análisis de cultivos año a año
5. Utiliza el selector de campaña para ver diferentes años
6. Exporta los resultados a CSV si lo deseas

## Solución de problemas

- **Error de autenticación con Earth Engine**: Ejecuta `earthengine authenticate` en la línea de comandos
- **No se visualizan los mapas**: Verifica la instalación de folium y streamlit-folium
- **No se abren nuevas pestañas**: Verifica que tu navegador no esté bloqueando ventanas emergentes

## Notas

- La API de SENASA tiene un límite de consultas, así que se ha implementado un tiempo de espera entre solicitudes
- El análisis de cultivos utiliza los datos de Google Earth Engine desde la campaña 2019-2020 hasta 2023-2024
