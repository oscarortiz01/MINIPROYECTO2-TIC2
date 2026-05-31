import requests
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

session = requests.Session()

def obtener_lista_completa():
    print("Consultando el registro maestro de PokéAPI...")
    url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
    try:
        respuesta = session.get(url)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return [pokemon['name'] for pokemon in datos['results']]
        else:
            print("Error al conectar con la base de datos maestra.")
            return []
    except Exception as e:
        print(f"Error de conexión: {e}")
        return []

def extraer_datos_pokeapi(nombre):
    url_pokemon = f"https://pokeapi.co/api/v2/pokemon/{nombre}"
    try:
        response = session.get(url_pokemon, timeout=10)
        if response.status_code != 200:
            return f"❌ No se encontró a {nombre}"
            
        data = response.json()
        tipo_final = data['types'][0]['type']['name']
        hp_base = next((stat['base_stat'] for stat in data['stats'] if stat['stat']['name'] == 'hp'), 100)
        
        ataques_validos = []
        movimientos_muestra = random.sample(data['moves'], min(20, len(data['moves'])))
        
        for move_entry in movimientos_muestra:
            move_url = move_entry['move']['url']
            move_data = session.get(move_url, timeout=10).json()
            
            power = move_data.get('power')
            if power is not None and power > 0:
                
                # --- NUEVO FILTRO DE NOMBRES ---
                # 1. Intentamos buscar el idioma español ('es')
                nombre_es = next((n['name'] for n in move_data['names'] if n['language']['name'] == 'es'), None)
                
                # 2. Si no existe traducción al español en la API (ataques muy nuevos), 
                # tomamos el nombre interno, quitamos guiones y ponemos mayúsculas.
                if not nombre_es:
                    nombre_es = move_data['name'].replace('-', ' ').title()
                
                # Balanceo proporcional del daño
                dano_escalado = int(power * 0.4) 
                dano_pauta = max(15, min(45, dano_escalado))
                
                ataques_validos.append({"name": nombre_es, "damage": dano_pauta})
            
            if len(ataques_validos) == 2:
                break
                
        if len(ataques_validos) < 2:
            ataques_validos = [{"name": "Placaje", "damage": 20}, {"name": "Golpe Fuerte", "damage": 35}]

        img_url = data['sprites']['other']['official-artwork']['front_default']
        ruta_imagen_local = f"assets/{nombre}.png"
        if img_url and not os.path.exists(ruta_imagen_local): 
            with open(ruta_imagen_local, 'wb') as f:
                f.write(session.get(img_url).content)

        audio_url = data['cries'].get('latest')
        ruta_audio_local = f"assets/{nombre}.ogg"
        if audio_url and not os.path.exists(ruta_audio_local): 
            try:
                with open(ruta_audio_local, 'wb') as f:
                    f.write(session.get(audio_url).content)
            except:
                pass 

        datos_finales = {
            "name": nombre.capitalize(),
            "type": tipo_final,
            "hp": hp_base,
            "attacks": ataques_validos,
            "image_path": ruta_imagen_local
        }
        
        nombre_archivo = f"cartas/{nombre}.json"
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, ensure_ascii=False, indent=4)

        return f"✅ {nombre.capitalize()} procesado."

    except Exception as e:
        return f"❌ Error en {nombre}: {e}"

if __name__ == "__main__":
    for carpeta in ["cartas", "assets"]:
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            
    lista_pokemon = obtener_lista_completa()
    print(f"Se obtuvieron {len(lista_pokemon)} Pokémon. Iniciando limpieza de textos y balanceo...\n")
    
    completados = 0
    with ThreadPoolExecutor(max_workers=15) as executor:
        futuros = {executor.submit(extraer_datos_pokeapi, poke): poke for poke in lista_pokemon}
        for futuro in as_completed(futuros):
            completados += 1
            resultado = futuro.result()
            print(f"[{completados}/{len(lista_pokemon)}] {resultado}")
            
    print("\n🚀 ¡Extracción y formateo completado!")