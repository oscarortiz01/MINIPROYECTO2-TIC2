import sys
import serial
import time
import json
import os
import random
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QInputDialog, QMessageBox, QHBoxLayout,
                             QFrame, QProgressBar, QDialog)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize
import serial.tools.list_ports
from PyQt6.QtGui import QPixmap, QIcon

import pygame
from combat import CombatEngine

# =====================================================================
# HILO DE COMUNICACIÓN SERIAL (BACKEND)
# =====================================================================
class LectorSerial(QThread):
    mensaje_recibido = pyqtSignal(str)

    def __init__(self, puerto, baudrate=9600):
        super().__init__()
        self.puerto = puerto
        self.baudrate = baudrate
        self.serial = None
        self.corriendo = True

    def run(self):
        try:
            self.serial = serial.Serial(self.puerto, self.baudrate, timeout=1)
        except Exception as e:
            self.mensaje_recibido.emit(f"ERROR: {e}")
            return

        while self.corriendo:
            if self.serial and self.serial.in_waiting > 0:
                try:
                    mensaje = self.serial.readline().decode('utf-8').strip()
                    if mensaje:
                        self.mensaje_recibido.emit(mensaje)
                except Exception:
                    pass
            time.sleep(0.05)

    def enviar(self, texto):
        if self.serial and self.serial.is_open:
            self.serial.write((texto + '\n').encode('utf-8'))

    def detener(self):
        self.corriendo = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.quit()
        self.wait()

# =====================================================================
# WIDGET DE LA CARTA POKÉMON (FRONTEND)
# =====================================================================
class CartaPokemon(QFrame):
    ataque_lanzado = pyqtSignal(str, int)

    def __init__(self, ruta_json=None, datos_dict=None, hp_actual=None):
        super().__init__()
        self.botones_ataque = [] 
        if datos_dict:
            self.datos = datos_dict
        else:
            self.datos = self.cargar_datos(ruta_json)
            
        self.hp_actual = hp_actual if hp_actual is not None else self.datos.get("hp", 100)
        self.init_ui()

    def cargar_datos(self, ruta_json):
        if not ruta_json or not os.path.exists(ruta_json):
            return {"name": "Conectando...", "type": "normal", "hp": 100, "attacks": [], "image_path": ""}
        with open(ruta_json, 'r', encoding='utf-8') as archivo:
            return json.load(archivo)

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            CartaPokemon { background-color: #f8f8f8; border: 3px solid #333; border-radius: 10px; }
            QLabel { font-family: Arial; }
        """)
        self.setFixedWidth(260) 
        layout_principal = QVBoxLayout()

        lbl_nombre = QLabel(f"<span style='font-size: 14pt; font-weight: bold; color: black;'>{self.datos['name']}</span>")
        
        traduccion_tipos = {
            "normal": "NORMAL", "fire": "FUEGO", "water": "AGUA", "electric": "ELÉCTRICO",
            "grass": "PLANTA", "ice": "HIELO", "fighting": "LUCHA", "poison": "VENENO",
            "ground": "TIERRA", "flying": "VOLADOR", "psychic": "PSÍQUICO", "bug": "BICHO",
            "rock": "ROCA", "ghost": "FANTASMA", "dragon": "DRAGÓN", "dark": "SINIESTRO",
            "steel": "ACERO", "fairy": "HADA"
        }
        
        tipo_ingles = self.datos.get('type', 'normal').lower()
        tipo_es = traduccion_tipos.get(tipo_ingles, "NORMAL")
        
        lbl_tipo = QLabel(tipo_es)
        lbl_tipo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        colores_tipos = {
            "fire": "#EE8130", "water": "#6390F0", "grass": "#7AC74C", "electric": "#F7D02C",
            "poison": "#A33EA1", "dragon": "#6F35FC", "ghost": "#735797", "fighting": "#C22E28",
            "psychic": "#F95587", "dark": "#705848", "normal": "#A8A77A", "flying": "#A98FF3",
            "steel": "#B7B7CE", "fairy": "#D685AD", "ice": "#96D9D6", "ground": "#E2BF65", 
            "bug": "#A6B91A", "rock": "#B6A136"
        }
        color_fondo = colores_tipos.get(tipo_ingles, "#A8A77A")
        
        lbl_tipo.setStyleSheet(f"background-color: {color_fondo}; color: white; padding: 4px; font-weight: bold; border-radius: 5px;")
        
        layout_cabecera = QHBoxLayout()
        layout_cabecera.addWidget(lbl_nombre)
        layout_cabecera.addWidget(lbl_tipo)
        layout_principal.addLayout(layout_cabecera)

        self.lbl_imagen = QLabel(self)
        self.lbl_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_imagen.setFixedHeight(160)
        self.lbl_imagen.setStyleSheet("border: 2px solid #ccc; background-color: white; border-radius: 5px;")
        
        ruta_imagen = self.datos.get("image_path", "")
        if ruta_imagen and os.path.exists(ruta_imagen):
            pixmap = QPixmap(ruta_imagen)
            self.lbl_imagen.setPixmap(pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.lbl_imagen.setText("ESPERANDO\nDATOS...")
            self.lbl_imagen.setStyleSheet("border: 2px solid #ccc; background-color: white; border-radius: 5px; color: black;")
            
        layout_principal.addWidget(self.lbl_imagen)

        self.barra_hp = QProgressBar()
        self.barra_hp.setMaximum(self.datos["hp"])
        self.barra_hp.setValue(self.hp_actual)
        self.barra_hp.setFormat("%v / %m HP")
        self.barra_hp.setStyleSheet("QProgressBar { text-align: center; font-weight: bold; border: 1px solid black; border-radius: 3px; color: black;} QProgressBar::chunk { background-color: #28B463; }")
        layout_principal.addWidget(self.barra_hp)

        layout_ataques = QHBoxLayout()
        for ataque in self.datos["attacks"]:
            btn_ataque = QPushButton(f"{ataque['name']}\n💥 {ataque['damage']}")
            btn_ataque.setStyleSheet("background-color: #eee; border: 1px solid #aaa; padding: 5px; border-radius: 3px; color: black;")
            btn_ataque.clicked.connect(lambda checked, a=ataque['name'], d=ataque['damage']: self.ataque_lanzado.emit(a, d))
            layout_ataques.addWidget(btn_ataque)
            self.botones_ataque.append(btn_ataque) 
            
        layout_principal.addLayout(layout_ataques)

        # --- NUEVO: BOTÓN DE CAMBIO COMO IMAGEN DE CARTA ---
        self.btn_cambio = QPushButton()
        self.btn_cambio.setToolTip("Click aquí para Cambiar de Pokémon")
        self.btn_cambio.setCursor(Qt.CursorShape.PointingHandCursor)
        
        ruta_dorso = "dorso_carta.png"
        if os.path.exists(ruta_dorso):
            self.btn_cambio.setIcon(QIcon(ruta_dorso))
            self.btn_cambio.setIconSize(QSize(60, 84)) # Proporción para que se vea como carta real
            # Quitamos los bordes y el fondo gris genérico de Windows
            self.btn_cambio.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 20);
                    border-radius: 8px;
                }
            """)
        else:
            self.btn_cambio.setText("🔄 Cambiar Pokémon")
            self.btn_cambio.setStyleSheet("padding: 5px; color: black;")

        # Lo envolvemos en un layout horizontal para que quede perfectamente centrado
        layout_boton_cambio = QHBoxLayout()
        layout_boton_cambio.addStretch()
        layout_boton_cambio.addWidget(self.btn_cambio)
        layout_boton_cambio.addStretch()
        
        layout_principal.addLayout(layout_boton_cambio)
        self.setLayout(layout_principal)

    def recibir_dano(self, cantidad):
        self.hp_actual -= cantidad
        if self.hp_actual < 0: self.hp_actual = 0
        self.barra_hp.setValue(self.hp_actual)
        if self.hp_actual < (self.datos["hp"] * 0.3):
            self.barra_hp.setStyleSheet("QProgressBar { text-align: center; font-weight: bold; border: 1px solid black; border-radius: 3px; color: black;} QProgressBar::chunk { background-color: #E74C3C; }")

    def set_modo_enemigo(self):
        for btn in self.botones_ataque:
            btn.hide()
        self.btn_cambio.hide()

    def deshabilitar_ataques(self, deshabilitar=True):
        estado = not deshabilitar
        for btn in self.botones_ataque:
            btn.setEnabled(estado)
            color = "#eee" if estado else "#999"
            texto = "black" if estado else "#555"
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #aaa; padding: 5px; border-radius: 3px; color: {texto};")

# =====================================================================
# APLICACIÓN PRINCIPAL (TABLERO DE COMBATE)
# =====================================================================
class PingPongApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.motor_combate = CombatEngine()
        pygame.mixer.init()

        self.modo, ok_modo = QInputDialog.getItem(
            self, "Modo de Juego", "Selecciona el modo:", 
            ["1. Modo Entrenamiento (Offline vs IA)", "2. Modo Combate (Multijugador)"], 0, False
        )
        if not ok_modo: sys.exit()
        
        self.es_entrenamiento = "1" in self.modo
        self.puerto = None

        if self.es_entrenamiento:
            self.rol = "Jugador Local"
            self.mi_turno = True
        else:
            self.rol, ok_rol = QInputDialog.getItem(self, "Configuración", "Selecciona el rol:", ["Jugador 1 (Transmisor)", "Jugador 2 (Receptor)"], 0, False)
            if not ok_rol: sys.exit()

            puertos_disponibles = [puerto.device for puerto in serial.tools.list_ports.comports()]
            if not puertos_disponibles:
                QMessageBox.critical(self, "Error", "No se detectó Arduino. Conecta tu placa.")
                sys.exit()

            self.puerto, ok_puerto = QInputDialog.getItem(self, "Puerto", "Selecciona el puerto:", puertos_disponibles, 0, False)
            if not ok_puerto: sys.exit()
            
            self.mi_turno = "1" in self.rol

        self.generar_equipo()
        self.init_ui()
        
        if not self.es_entrenamiento and self.puerto:
            self.iniciar_serial()

    def showEvent(self, event):
        super().showEvent(event)
        
        if not getattr(self, 'audio_iniciado', False):
            self.audio_iniciado = True
            
            self.reproducir_musica_fondo()
            
            if self.es_entrenamiento:
                QTimer.singleShot(300, lambda: self.reproducir_grito(self.mi_equipo[self.idx_activo]["nombre"]))
                QTimer.singleShot(1000, lambda: self.reproducir_grito(self.carta_rival.datos['name']))

    # ================== MÉTODOS DE AUDIO ==================
    def reproducir_musica_fondo(self):
        ruta_musica = "assets/combate.mp3"
        if os.path.exists(ruta_musica):
            try:
                pygame.mixer.music.load(ruta_musica)
                pygame.mixer.music.set_volume(0.3) 
                pygame.mixer.music.play(-1) 
            except Exception as e:
                print("Error cargando música:", e)

    def reproducir_grito(self, nombre_pokemon):
        nombre_limpio = nombre_pokemon.lower().replace("dummy ", "")
        ruta_mp3 = f"assets/{nombre_limpio}.mp3"
        ruta_wav = f"assets/{nombre_limpio}.wav"
        ruta_ogg = f"assets/{nombre_limpio}.ogg"
        
        ruta_final = None
        if os.path.exists(ruta_mp3): ruta_final = ruta_mp3
        elif os.path.exists(ruta_wav): ruta_final = ruta_wav
        elif os.path.exists(ruta_ogg): ruta_final = ruta_ogg
        
        if ruta_final:
            try:
                grito = pygame.mixer.Sound(ruta_final)
                grito.set_volume(1.0)
                grito.play()
            except Exception as e:
                print(f"Error reproduciendo grito de {nombre_limpio}: {e}")
    # ======================================================

    def generar_equipo(self):
        carpeta = "cartas"
        archivos = [f for f in os.listdir(carpeta) if f.endswith('.json')]
        archivos.sort() 
        
        if self.es_entrenamiento:
            pool = archivos
        else:
            mitad = len(archivos) // 2
            pool = archivos[:mitad] if "1" in self.rol else archivos[mitad:]
        
        seleccionados = random.sample(pool, min(6, len(pool)))
        self.mi_equipo = []
        for arch in seleccionados:
            ruta = os.path.join(carpeta, arch)
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                self.mi_equipo.append({
                    "ruta": ruta, "nombre": datos["name"], "tipo": datos["type"],
                    "hp_max": datos["hp"], "hp_actual": datos["hp"]
                })
            except Exception:
                pass
        self.idx_activo = 0 

    def generar_dummy(self):
        carpeta = "cartas"
        archivos = [f for f in os.listdir(carpeta) if f.endswith('.json')]
        if archivos:
            archivo_azar = random.choice(archivos)
            ruta = os.path.join(carpeta, archivo_azar)
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos_base = json.load(f)
            except:
                datos_base = {"name": "Desconocido", "type": "normal", "image_path": "", "attacks": []}
        else:
            datos_base = {"name": "Desconocido", "type": "normal", "image_path": "", "attacks": []}

        hp_dummy = random.randint(80, 150)
        ataques_dummy = []
        nombres_genericos = ["Placaje", "Arañazo", "Mordisco", "Derribo"]
        
        for i in range(2):
            if "attacks" in datos_base and i < len(datos_base["attacks"]):
                nombre_atk = datos_base["attacks"][i]["name"]
            else:
                nombre_atk = random.choice(nombres_genericos)
            
            ataques_dummy.append({
                "name": nombre_atk, 
                "damage": random.randint(15, 45)
            })

        return {
            "name": f"Dummy {datos_base['name']}",
            "type": datos_base.get('type', 'normal'),
            "hp": hp_dummy, 
            "attacks": ataques_dummy,
            "image_path": datos_base.get('image_path', '') 
        }

    def init_ui(self):
        self.setWindowTitle(f"PokéDuel - {self.modo}")
        self.resize(850, 550) 
        
        self.setStyleSheet("""
            PingPongApp { background-color: #1E2A38; border: 5px solid #0F161E; }
            QLabel#titulo { 
                color: #FFCB05; 
                font-size: 18pt; 
                font-weight: bold; 
                background-color: #3B4CCA; 
                padding: 8px; 
                border-radius: 5px;
                border: 2px solid #FFCB05;
            }
            QLabel#log { 
                color: #FFFFFF; 
                font-size: 12pt; 
                background-color: #2A3B4C; 
                padding: 15px; 
                border-radius: 8px;
                border: 2px solid #455A64;
            }
        """)

        layout_principal = QVBoxLayout()
        cabecera_layout = QHBoxLayout()
        lbl_titulo = QLabel("ÁRENA DE ENTRENAMIENTO" if self.es_entrenamiento else "ÁRENA DE COMBATE", self)
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_indicador = QLabel("OFFLINE (ENTRENAMIENTO)" if self.es_entrenamiento else "ESPERANDO CONEXIÓN", self)
        color_ind = "gray" if self.es_entrenamiento else "orange"
        self.lbl_indicador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_indicador.setStyleSheet(f"background-color: {color_ind}; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        
        cabecera_layout.addWidget(lbl_titulo)
        cabecera_layout.addWidget(self.lbl_indicador)
        layout_principal.addLayout(cabecera_layout)

        self.lbl_turno = QLabel()
        self.lbl_turno.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(self.lbl_turno)

        tablero_layout = QHBoxLayout()

        self.layout_izq = QVBoxLayout()
        lbl_tu = QLabel("TU PUESTO ACTIVO", self)
        lbl_tu.setStyleSheet("color: #FFCB05; font-weight: bold; font-size: 14pt;")
        lbl_tu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_izq.addWidget(lbl_tu)
        
        self.carta_jugador = CartaPokemon(ruta_json=self.mi_equipo[self.idx_activo]["ruta"], hp_actual=self.mi_equipo[self.idx_activo]["hp_actual"]) 
        self.carta_jugador.ataque_lanzado.connect(self.procesar_envio_ataque)
        self.carta_jugador.btn_cambio.clicked.connect(self.abrir_menu_cambio)
        self.layout_izq.addWidget(self.carta_jugador)

        msg_inicio = "Comienza la partida. ¡Analiza tus ataques!" if self.es_entrenamiento else "Sincronizando automáticamente..."
        self.lbl_estado = QLabel(msg_inicio, self)
        self.lbl_estado.setObjectName("log")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setFixedWidth(240)

        self.layout_der = QVBoxLayout()
        lbl_rival = QLabel("PUESTO RIVAL" if self.es_entrenamiento else "PUESTO RIVAL", self)
        lbl_rival.setStyleSheet("color: #FF7043; font-weight: bold; font-size: 14pt;")
        lbl_rival.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_der.addWidget(lbl_rival)

        if self.es_entrenamiento:
            datos_dummy = self.generar_dummy()
            self.carta_rival = CartaPokemon(datos_dict=datos_dummy) 
        else:
            self.carta_rival = CartaPokemon(ruta_json="none.json")
            
        self.carta_rival.set_modo_enemigo() 
        self.layout_der.addWidget(self.carta_rival)

        tablero_layout.addLayout(self.layout_izq)
        tablero_layout.addWidget(self.lbl_estado)
        tablero_layout.addLayout(self.layout_der)

        layout_principal.addLayout(tablero_layout)
        self.setLayout(layout_principal)

        self.actualizar_ui_turno()

    # ================== MÉTODOS DE REINICIO DE PARTIDA ==================
    def accion_jugar_otra_vez_mismo_modo(self):
        self.dialogo_fin.accept()
        self.resetear_partida_mismo_modo()
        
    def accion_cambiar_modo(self):
        self.dialogo_fin.accept()
        self.cambiar_modo_juego()

    def cambiar_modo_juego(self):
        if hasattr(self, 'hilo_serial'):
            self.hilo_serial.detener()
        pygame.mixer.quit() 
        os.execl(sys.executable, sys.executable, *sys.argv)

    def resetear_partida_mismo_modo(self):
        self.generar_equipo()
        self.mi_turno = True if self.es_entrenamiento else ("1" in self.rol)
        
        self.actualizar_mi_carta()
        
        self.layout_der.removeWidget(self.carta_rival)
        self.carta_rival.deleteLater()
        
        if self.es_entrenamiento:
            datos_dummy = self.generar_dummy()
            self.carta_rival = CartaPokemon(datos_dict=datos_dummy) 
        else:
            self.carta_rival = CartaPokemon(ruta_json="none.json")
            
        self.carta_rival.set_modo_enemigo() 
        self.layout_der.addWidget(self.carta_rival)
        
        msg_inicio = "Comienza la partida. ¡Analiza tus ataques!" if self.es_entrenamiento else "Sincronizando automáticamente..."
        self.lbl_estado.setText(msg_inicio)
        self.actualizar_ui_turno()
        
        if self.es_entrenamiento:
            QTimer.singleShot(800, lambda: self.reproducir_grito(self.mi_equipo[self.idx_activo]["nombre"]))
            QTimer.singleShot(1500, lambda: self.reproducir_grito(self.carta_rival.datos['name']))
        else:
            QTimer.singleShot(1000, self.enviar_sincronizacion)
            QTimer.singleShot(3000, self.enviar_sincronizacion)
            QTimer.singleShot(5000, self.enviar_sincronizacion)

    # ================== RESULTADO DE LA PARTIDA ==================
    def mostrar_resultado(self, victoria):
        self.dialogo_fin = QDialog(self)
        self.dialogo_fin.setWindowTitle("¡Fin del Combate!")
        self.dialogo_fin.setStyleSheet("background-color: white;")
        layout = QVBoxLayout()
        
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_img = "ganador.png" if victoria else "perdedor.png"
        
        if os.path.exists(ruta_img):
            pix = QPixmap(ruta_img)
            lbl_img.setPixmap(pix.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            lbl_img.setText(f"⚠️ Guarda una imagen llamada\n'{ruta_img}' en tu carpeta\npara verla aquí.")
            lbl_img.setStyleSheet("color: black; font-weight: bold; border: 2px dashed red; padding: 20px; font-size: 12pt;")
        
        lbl_msg = QLabel("¡HAS GANADO LA PARTIDA!" if victoria else "¡HAS PERDIDO LA PARTIDA!")
        color_texto = "green" if victoria else "red"
        lbl_msg.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {color_texto};")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_botones = QHBoxLayout()
        
        btn_reiniciar_mismo = QPushButton("🔄 Jugar Otra Vez (Mismo Modo)")
        btn_reiniciar_mismo.setStyleSheet("background-color: #28B463; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_reiniciar_mismo.clicked.connect(self.accion_jugar_otra_vez_mismo_modo)
        
        btn_cambiar_modo = QPushButton("⚙️ Cambiar de Modo")
        btn_cambiar_modo.setStyleSheet("background-color: #F39C12; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_cambiar_modo.clicked.connect(self.accion_cambiar_modo)
        
        btn_cerrar = QPushButton("❌ Salir del Juego")
        btn_cerrar.setStyleSheet("background-color: #333; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_cerrar.clicked.connect(self.close)
        
        layout_botones.addWidget(btn_reiniciar_mismo)
        layout_botones.addWidget(btn_cambiar_modo)
        layout_botones.addWidget(btn_cerrar)
        
        layout.addWidget(lbl_img)
        layout.addWidget(lbl_msg)
        layout.addLayout(layout_botones)
        
        self.dialogo_fin.setLayout(layout)
        self.dialogo_fin.exec()

    def actualizar_ui_turno(self):
        vivo = self.mi_equipo[self.idx_activo]["hp_actual"] > 0

        if self.mi_turno:
            self.lbl_turno.setText("🟩 ¡ES TU TURNO! 🟩")
            self.lbl_turno.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; font-size: 14pt; padding: 5px; border-radius: 5px;")
            self.carta_jugador.deshabilitar_ataques(not vivo) 
            self.carta_jugador.btn_cambio.setEnabled(True)
        else:
            self.lbl_turno.setText("🟥 TURNO DEL RIVAL... 🟥")
            self.lbl_turno.setStyleSheet("background-color: #C0392B; color: white; font-weight: bold; font-size: 14pt; padding: 5px; border-radius: 5px;")
            self.carta_jugador.deshabilitar_ataques(True)
            self.carta_jugador.btn_cambio.setEnabled(not vivo) 

    def iniciar_serial(self):
        self.hilo_serial = LectorSerial(self.puerto.strip().upper())
        self.hilo_serial.mensaje_recibido.connect(self.procesar_mensaje_entrante)
        self.hilo_serial.start()
        self.lbl_indicador.setText("CONECTADO")
        self.lbl_indicador.setStyleSheet("background-color: green; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        
        QTimer.singleShot(3500, self.enviar_sincronizacion)
        QTimer.singleShot(4500, self.enviar_sincronizacion)

    def enviar_sincronizacion(self):
        if hasattr(self, 'hilo_serial') and self.hilo_serial.serial.is_open:
            nombre = self.mi_equipo[self.idx_activo]["nombre"]
            self.hilo_serial.enviar(f"READY|{nombre}")
            self.lbl_estado.setText("Datos enviados.\nEsperando al oponente...")
            self.reproducir_grito(nombre)

    def abrir_menu_cambio(self):
        opciones = []
        indices_validos = []
        for i, poke in enumerate(self.mi_equipo):
            if poke["hp_actual"] > 0 and i != self.idx_activo:
                opciones.append(f"{poke['nombre']} ({poke['hp_actual']}/{poke['hp_max']} HP)")
                indices_validos.append(i)
                
        if not opciones:
            QMessageBox.warning(self, "Sin opciones", "No te quedan más Pokémon con vida.")
            return

        seleccion, ok = QInputDialog.getItem(self, "Cambio de Pokémon", "Elige tu relevo:", opciones, 0, False)
        if ok and seleccion:
            estaba_muerto = self.mi_equipo[self.idx_activo]["hp_actual"] <= 0
            
            self.idx_activo = indices_validos[opciones.index(seleccion)]
            self.actualizar_mi_carta()
            
            nombre_nuevo = self.mi_equipo[self.idx_activo]["nombre"]
            self.reproducir_grito(nombre_nuevo)

            if not self.es_entrenamiento:
                if estaba_muerto:
                    self.hilo_serial.enviar(f"SWAP_FORZADO|{nombre_nuevo}")
                    self.mi_turno = True
                else:
                    self.hilo_serial.enviar(f"SWAP_VOLUNTARIO|{nombre_nuevo}")
                    self.mi_turno = False
            else:
                self.mi_turno = estaba_muerto
            
            self.lbl_estado.setText(f"¡Adelante {nombre_nuevo}!")
            self.actualizar_ui_turno()

            if self.es_entrenamiento and not estaba_muerto:
                QTimer.singleShot(1500, self.turno_ia_dummy)

    def actualizar_mi_carta(self):
        self.layout_izq.removeWidget(self.carta_jugador)
        self.carta_jugador.deleteLater()
        p_actual = self.mi_equipo[self.idx_activo]
        self.carta_jugador = CartaPokemon(ruta_json=p_actual["ruta"], hp_actual=p_actual["hp_actual"])
        self.carta_jugador.ataque_lanzado.connect(self.procesar_envio_ataque)
        self.carta_jugador.btn_cambio.clicked.connect(self.abrir_menu_cambio)
        self.layout_izq.addWidget(self.carta_jugador)
        self.verificar_muerte()

    def procesar_envio_ataque(self, nombre_ataque, dano_base):
        mi_tipo = self.mi_equipo[self.idx_activo]["tipo"]
        tipo_rival = self.carta_rival.datos["type"]
        
        dano_final, m = self.motor_combate.calcular_danio(mi_tipo, tipo_rival, dano_base)
        
        texto_ventaja = ""
        if m > 1.0: texto_ventaja = "\n¡Es súper efectivo! (x2)"
        elif m < 1.0: texto_ventaja = "\nNo es muy efectivo... (x0.5)"
        elif m == 0.0: texto_ventaja = "\n¡No tiene efecto! (x0)"

        self.lbl_estado.setText(f"¡Atacaste con {nombre_ataque}!\nDaño: {dano_final} {texto_ventaja}")
        
        hp_anterior_rival = self.carta_rival.hp_actual
        self.carta_rival.recibir_dano(dano_final)
        if hp_anterior_rival > 0 and self.carta_rival.hp_actual <= 0:
            self.reproducir_grito(self.carta_rival.datos['name'])

        self.mi_turno = False
        self.actualizar_ui_turno()

        if self.es_entrenamiento:
            if self.carta_rival.hp_actual <= 0:
                self.mostrar_resultado(victoria=True)
            else:
                QTimer.singleShot(2000, self.turno_ia_dummy)
        else:
            trama_datos = f"ATK|{nombre_ataque}|{dano_final}"
            if hasattr(self, 'hilo_serial'):
                self.hilo_serial.enviar(trama_datos)

    def turno_ia_dummy(self):
        ataques = self.carta_rival.datos['attacks']
        tipo_dummy = self.carta_rival.datos['type']
        mi_tipo = self.mi_equipo[self.idx_activo]["tipo"]
        
        mejor_ataque = ataques[0]
        max_dano = 0
        mejor_m = 1.0
        
        for atk in ataques:
            dano_calculado, m = self.motor_combate.calcular_danio(tipo_dummy, mi_tipo, atk['damage'])
            if dano_calculado >= max_dano:
                max_dano = dano_calculado
                mejor_ataque = atk
                mejor_m = m

        texto_ventaja = ""
        if mejor_m > 1.0: texto_ventaja = "\n¡Es súper efectivo! (x2)"
        elif mejor_m < 1.0: texto_ventaja = "\nNo es muy efectivo... (x0.5)"
        elif mejor_m == 0.0: texto_ventaja = "\n¡No tiene efecto! (x0)"

        self.lbl_estado.setText(f"¡El Dummy usó {mejor_ataque['name']}!\nRecibes {max_dano} de daño. {texto_ventaja}")
        
        hp_anterior = self.mi_equipo[self.idx_activo]["hp_actual"]
        self.carta_jugador.recibir_dano(max_dano)
        self.mi_equipo[self.idx_activo]["hp_actual"] -= max_dano
        
        if hp_anterior > 0 and self.mi_equipo[self.idx_activo]["hp_actual"] <= 0:
            self.reproducir_grito(self.mi_equipo[self.idx_activo]["nombre"])
        
        self.mi_turno = True
        self.actualizar_ui_turno()
        self.verificar_muerte()

    def procesar_mensaje_entrante(self, mensaje):
        if "ERROR" in mensaje:
            self.actualizar_indicador("ERROR SERIAL", "darkred", "white")
            return

        if mensaje.startswith("READY|"):
            _, nombre_pokemon = mensaje.split("|")
            ruta = f"cartas/{nombre_pokemon.lower()}.json"
            self.layout_der.removeWidget(self.carta_rival)
            self.carta_rival.deleteLater()
            self.carta_rival = CartaPokemon(ruta_json=ruta)
            self.carta_rival.set_modo_enemigo()
            self.layout_der.addWidget(self.carta_rival)
            self.lbl_estado.setText(f"El rival está listo con {nombre_pokemon}.")
            
            self.reproducir_grito(nombre_pokemon)

        elif mensaje.startswith("SWAP_VOLUNTARIO|") or mensaje.startswith("SWAP_FORZADO|"):
            _, nombre_pokemon = mensaje.split("|")
            ruta = f"cartas/{nombre_pokemon.lower()}.json"
            self.layout_der.removeWidget(self.carta_rival)
            self.carta_rival.deleteLater()
            self.carta_rival = CartaPokemon(ruta_json=ruta)
            self.carta_rival.set_modo_enemigo()
            self.layout_der.addWidget(self.carta_rival)
            
            if "FORZADO" in mensaje:
                self.lbl_estado.setText(f"¡El rival sacó a {nombre_pokemon} tras ser debilitado!")
                self.mi_turno = False
            else:
                self.lbl_estado.setText(f"¡El rival cambió a {nombre_pokemon}!")
                self.mi_turno = True
            
            self.reproducir_grito(nombre_pokemon)
            self.actualizar_ui_turno()

        elif mensaje.startswith("ATK|"):
            try:
                _, nombre_ataque, dano = mensaje.split("|")
                dano_int = int(dano)
                self.lbl_estado.setText(f"¡El rival usó {nombre_ataque}!\nRecibes {dano_int} de daño.")
                
                hp_anterior = self.mi_equipo[self.idx_activo]["hp_actual"]
                self.carta_jugador.recibir_dano(dano_int)
                self.mi_equipo[self.idx_activo]["hp_actual"] -= dano_int
                
                if hp_anterior > 0 and self.mi_equipo[self.idx_activo]["hp_actual"] <= 0:
                    self.reproducir_grito(self.mi_equipo[self.idx_activo]["nombre"])
                
                self.mi_turno = True
                self.actualizar_ui_turno()
                self.verificar_muerte()
            except ValueError:
                pass
                
        elif mensaje.startswith("GAME_OVER|"):
            self.lbl_estado.setText("¡El rival no tiene más Pokémon!")
            self.mostrar_resultado(victoria=True)

    def verificar_muerte(self):
        if self.mi_equipo[self.idx_activo]["hp_actual"] <= 0:
            self.mi_equipo[self.idx_activo]["hp_actual"] = 0
            self.carta_jugador.deshabilitar_ataques(True)
            self.carta_jugador.btn_cambio.setEnabled(True) 
            
            vivos = sum(1 for p in self.mi_equipo if p["hp_actual"] > 0)
            if vivos == 0:
                self.lbl_estado.setText("¡Te has quedado sin Pokémon!")
                if not self.es_entrenamiento:
                    if hasattr(self, 'hilo_serial'):
                        self.hilo_serial.enviar("GAME_OVER|")
                self.mostrar_resultado(victoria=False)
            else:
                self.lbl_estado.setText("¡Tu Pokémon se debilitó!\nDebes cambiar a otro.")

    def closeEvent(self, event):
        if hasattr(self, 'hilo_serial'):
            self.hilo_serial.detener()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PingPongApp()
    ventana.show()
    sys.exit(app.exec())