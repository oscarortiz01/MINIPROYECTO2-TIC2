# MiniProyecto 2: PokéDuel

Este repositorio contiene todos nuestros entregables para el MiniProyecto 2.

## Contenido del Repositorio

* [Mini_Proyecto_2.pdf](/Mini_Proyecto_2.pdf): Nuestro informe completo del proyecto en formato PDF.
* [pokeduel.py](/pokeduel.py): Aplicación principal (Frontend) donde programamos la interfaz gráfica inmersiva en PyQt6 y la gestión del flujo multijugador.
* [combat.py](/combat.py): Motor lógico (Backend) de combate que desarrollamos, el cual incluye la matriz oficial de los 18 tipos y la Inteligencia Artificial del oponente (Dummy).
* [generar_cartas.py](/generar_cartas.py): Script de Web Scraping concurrente que creamos para extraer, filtrar y normalizar los datos de los 1025 Pokémon desde la PokéAPI oficial.
* [ping_pong.py](/ping_pong.py): Prueba de concepto aislada que utilizamos para validar el enlace bidireccional asíncrono del puerto Serial.
* [pokeduel.ino](/pokeduel.ino): Firmware en C++ para las placas Arduino que configuramos para actuar como puente de comunicación (Serial ↔ I2C).
* **Carpeta `cartas/`**: Base de datos local en formato JSON que generamos con las estadísticas y ataques balanceados de los Pokémon.
* **Carpeta `assets/`**: Recursos multimedia que implementamos en el código, incluyendo sprites oficiales, gritos de batalla (.ogg) y la banda sonora del simulador.

## Video de Demostración

En el siguiente enlace se encuentra el video demostrativo donde se enseña el funcionamiento de la prueba Ping-Pong, el modo Entrenamiento y el Combate multijugador entre dos computadores, destacando la interacción bidireccional entre la interfaz gráfica y el hardware asociado (Arduino e I2C).

⦁ Video de Demostración en YouTube
  https://youtu.be/cklyOgzhCMc

  Integrantes:
* Oscar Ortiz Molina
* Joaquín Mardones Gallegos




