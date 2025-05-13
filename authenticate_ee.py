import ee
import webbrowser
import os

# Intenta inicializar sin autenticación primero
try:
    ee.Initialize()
    print("Ya estás autenticado con Earth Engine.")
except Exception as e:
    print("Necesitas autenticarte con Earth Engine.")
    
    # Usar método de autenticación alternativo
    auth_url = ee.oauth.get_authorization_url()
    print("Abre este URL en tu navegador para autenticarte:")
    print(auth_url)
    
    # Intentar abrir el navegador automáticamente (puede que no funcione en todos los entornos)
    try:
        webbrowser.open_new(auth_url)
    except:
        pass
    
    # Pedir código de autorización
    auth_code = input("Pega el código de autorización aquí: ")
    
    # Autenticar con el código
    token = ee.oauth.request_token(auth_code)
    ee.oauth.write_token(token)
    
    # Verificar autenticación
    try:
        ee.Initialize()
        print("¡Autenticación exitosa!")
    except Exception as e:
        print(f"Error durante la autenticación: {str(e)}")
