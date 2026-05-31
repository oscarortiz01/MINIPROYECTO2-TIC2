import sys
import serial
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QInputDialog, QMessageBox, QTextEdit)
from PyQt6.QtCore import QThread, pyqtSignal
import serial.tools.list_ports

# =====================================================================
# HILO DE COMUNICACIÓN SERIAL (Aislado para Actividad 1.1)
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
# INTERFAZ GRÁFICA DEL PING-PONG
# =====================================================================
class PingPongApp(QWidget):
    def __init__(self):
        super().__init__()
        
        puertos_disponibles = [puerto.device for puerto in serial.tools.list_ports.comports()]
        if not puertos_disponibles:
            QMessageBox.critical(self, "Error", "No se detectó ningún puerto serial (Arduino).")
            sys.exit()

        self.puerto, ok = QInputDialog.getItem(self, "Selección de Puerto", "Elige el puerto COM:", puertos_disponibles, 0, False)
        if not ok: sys.exit()

        self.init_ui()
        self.iniciar_serial()

    def init_ui(self):
        self.setWindowTitle("Actividad 1.1 - Test de Ping-Pong Serial")
        self.resize(400, 300)
        # Se fuerza el color de texto a negro en toda la ventana
        self.setStyleSheet("background-color: #f0f0f0; color: black; font-family: Arial;")

        layout = QVBoxLayout()

        self.lbl_estado = QLabel(f"Conectado a {self.puerto}")
        self.lbl_estado.setStyleSheet("color: green; font-weight: bold; font-size: 14pt;")
        layout.addWidget(self.lbl_estado)

        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        # Se asegura fondo blanco y texto negro explícitamente con letra más grande
        self.consola.setStyleSheet("background-color: white; color: black; border: 1px solid #ccc; font-size: 12pt;")
        layout.addWidget(self.consola)

        self.btn_ping = QPushButton("Enviar PING")
        self.btn_ping.setStyleSheet("background-color: #007BFF; color: white; padding: 10px; font-weight: bold; font-size: 12pt;")
        self.btn_ping.clicked.connect(self.enviar_ping)
        layout.addWidget(self.btn_ping)

        self.setLayout(layout)

    def iniciar_serial(self):
        self.hilo_serial = LectorSerial(self.puerto)
        self.hilo_serial.mensaje_recibido.connect(self.procesar_mensaje)
        self.hilo_serial.start()
        self.registrar_log("Sistema iniciado. Esperando mensajes...")

    def enviar_ping(self):
        """Envia el mensaje inicial PING por el puerto serial"""
        if hasattr(self, 'hilo_serial'):
            self.hilo_serial.enviar("PING")
            self.registrar_log("📤 ENVIADO: PING")

    def procesar_mensaje(self, mensaje):
        """Procesa lo que llega del otro computador"""
        if "ERROR" in mensaje:
            self.registrar_log(f"❌ {mensaje}")
            self.lbl_estado.setStyleSheet("color: red; font-weight: bold; font-size: 14pt;")
            return

        self.registrar_log(f"📥 RECIBIDO: {mensaje}")

        if mensaje == "PING":
            time.sleep(0.5) 
            self.hilo_serial.enviar("PONG")
            self.registrar_log("📤 AUTO-RESPUESTA ENVIADA: PONG")

    def registrar_log(self, texto):
        """Agrega texto a la consola de la interfaz"""
        self.consola.append(texto)

    def closeEvent(self, event):
        """Cierra el puerto serial al cerrar la ventana"""
        if hasattr(self, 'hilo_serial'):
            self.hilo_serial.detener()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PingPongApp()
    ventana.show()
    sys.exit(app.exec())