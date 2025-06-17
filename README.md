![Banner de searchCommand](https://i.imgur.com/NII8Wbr.jpeg)

<div align="center"> <h3>Herramienta de búsqueda interactiva para comandos de pentesting y GTFOBins en Linux</h3>

[![Versión](https://img.shields.io/badge/versi%C3%B3n-0.2-blue.svg)](https://github.com/SkyW4r33x/searchCommand) [![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://python.org/) [![Licencia](https://img.shields.io/badge/licencia-MIT-red.svg)](https://github.com/SkyW4r33x/searchCommand/blob/main/LICENSE) [![Plataforma](https://img.shields.io/badge/plataforma-Linux-orange.svg)](https://www.linux.org/)

</div>

## Tabla de Contenido

- [Descripción](#descripción)
- [Características](#características)
- [Instalación](#instalación)
  - [Importante para usuarios existentes](#importante-para-usuarios-existentes)
  - [Prerrequisitos](#prerrequisitos)
  - [Pasos de instalación](#pasos-de-instalación)
- [Uso](#uso)
  - [searchCommand - Modo interactivo](#searchcommand---modo-interactivo)
  - [gtfsearch - GTFOBins Local](#gtfsearch---gtfobins-local)
- [Configuración](#configuración)
  - [Formato de utilscommon](#formato-de-utilscommon)
  - [Estructura de archivos](#estructura-de-archivos)
- [Capturas de pantalla](#capturas-de-pantalla)
- [Terminales compatibles](#terminales-compatibles)
- [Distribuciones soportadas](#distribuciones-soportadas)
- [Desinstalación](#desinstalación)
- [Problemas conocidos](#problemas-conocidos)
- [Contribuciones](#contribuciones)
- [Créditos](#créditos)
- [Autor](#autor)

## Descripción

**searchCommand** es una herramienta escrita en Python diseñada para pentesters y entusiastas de la seguridad informática. Permite buscar y explorar comandos organizados por categorías y herramientas de manera interactiva, con autocompletado, resaltado de sintaxis y un diseño inspirado en Kali Linux.

### Nueva funcionalidad

Ahora incluye **gtfsearch** para acceso local a GTFOBins, permitiendo consultas offline de técnicas de escalación de privilegios y bypass de restricciones.

## Características

| Característica | Descripción |
|---|---|
| **Interfaz interactiva** | Busca comandos con un prompt estilo Kali, con soporte para autocompletado (Tab) y atajos de teclado |
| **Categorías y herramientas** | Organiza comandos en categorías definidas en `utilscommon` para fácil acceso |
| **Resaltado de sintaxis** | Colorea comandos, parámetros y comentarios para mayor claridad |
| **Sugerencias inteligentes** | Si no encuentras un comando, te sugiere opciones similares |
| **GTFOBins integrado** | Accede a GTFOBins de forma local con `gtfsearch` |
| **Personalizable** | Usa un archivo `utilscommon` para definir tus propios comandos y categorías |

## Instalación

### Importante para usuarios existentes

**Si ya tienes searchCommand instalado y quieres acceder a la nueva funcionalidad `gtfsearch`, debes realizar una instalación limpia:**

1. **Desinstala la versión anterior:**

   ```bash
   sudo ./kali-install.py
   # Selecciona [4] Desinstalar searchCommand
   ```

2. **Descarga la nueva versión:**

   ```bash
   git clone https://github.com/SkyW4r33x/searchCommand.git
   cd searchCommand
   ```

3. **Instala la nueva versión siguiendo los pasos de instalación.**

> **Importante**: La actualización directa desde searchCommand no incluye gtfsearch. Es necesario descargar el repositorio completo para acceder a todas las funcionalidades.

### Prerrequisitos - usuarios nuevos.

Asegúrate de tener Python 3 con `venv` y `pip`. En Kali Linux, esto suele venir preinstalado. Si no:

```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

### Pasos de instalación

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/SkyW4r33x/searchCommand.git
   cd searchCommand
   ```

2. **Ejecuta el instalador:**

   ```bash
   chmod +x kali-install.py
   sudo ./kali-install.py
   ```

   - Selecciona `[1] Instalar searchCommand` en el menú

## Uso

### searchCommand - Modo interactivo

Ejecuta `searchCommand` sin argumentos para entrar en el modo interactivo:

```bash
searchCommand
```

#### Comandos internos

| Comando               | Alias | Descripción                              |
|-----------------------|-------|------------------------------------------|
| `<herramienta>`       | -     | Buscar una herramienta (ej: NMAP)       |
| `<categoría>`         | -     | Buscar una categoría (ej: RECONOCIMIENTO)|
| `gtfsearch`           | `gtf` | Buscar en GTFOBins                      |
| `help`                | `h`   | Mostrar este menú de ayuda              |
| `list tools`          | `lt`  | Listar todas las herramientas           |
| `list categories`     | `lc`  | Listar todas las categorías             |
| `setip <IP>`          | `si`  | Configurar $IP                          |
| `seturl <URL>`        | `su`  | Configurar $URL                         |
| `edit <herramienta>`  | `e`   | Editar herramienta                      |
| `refresh [config]`    | `r`   | Recargar herramientas o limpiar config  |
| `update [-r]`         | `u`   | Actualizar o restaurar versión anterior |
| `clear`               | `c`   | Limpiar la pantalla                     |
| `exit`                | `q`   | Salir del programa                      |

#### Atajos de teclado

| Atajo       | Descripción                              |
|-------------|------------------------------------------|
| `Tab`       | Autocompletar categorías o herramientas |
| `Ctrl + L`  | Limpiar pantalla                        |
| `Ctrl + T`  | Listar herramientas rápidamente         |
| `Ctrl + K`  | Listar categorías rápidamente           |
| `Ctrl + E`  | Editar última herramienta buscada       |
| `Ctrl + R`  | Recargar herramientas                   |
| `Ctrl + C`  | Salir inmediatamente                    |

#### Búsqueda directa

```bash
searchCommand -q nmap
```

### gtfsearch - GTFOBins Local

**gtfsearch** te permite acceder a la base de datos de GTFOBins de forma local y offline.
<h2> Capturas de gtfsearch</h2>

| Funcionalidad | Captura |
|---|---|
| **Ayuda** | ![Ayuda gtfsearch](https://imgur.com/xmZEIAN.png) |
| **Lista de binarios** | ![Lista binarios](https://imgur.com/6tC6u4U.png) |
| **Información del binario** | ![Ejemplo binario](https://imgur.com/rZRjXzR.png) |
| **Autocompletado** | ![Autocompletado](https://imgur.com/9cq2GAC.png) |

## Configuración

### Formato de utilscommon

La herramienta `utilscommon` organiza los comandos en una estructura de carpetas dentro del directorio `~/referencestuff`.

#### Inicializar utilscommon

Si el directorio `~/referencestuff` no existe, créalo con:

```bash
mkdir -p ~/referencestuff
```

Crea un archivo para una herramienta, por ejemplo:

```bash
mkdir ~/referencestuff/RECONOCIMIENTO
echo -e "Descripción:▶ Escaneo Rápido (Puertos abiertos rápidamente):\nComando: nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn \$IP -oG allPorts" > ~/referencestuff/RECONOCIMIENTO/NMAP.txt
```

### Estructura de archivos

```bash
~/referencestuff/
├── RECONOCIMIENTO/
│   ├── NMAP.txt
│   └── OTRA_HERRAMIENTA.txt
├── EXPLOTACIÓN/
│   ├── METASPLOIT.txt
│   └── OTRA_HERRAMIENTA.txt
└── 
```

#### Formato de archivo de herramienta

Cada archivo debe seguir este formato:

```bash
Descripción:▶ [Descripción del comando]
Comando: [Comando completo]
```

**Ejemplo** (`~/referencestuff/RECONOCIMIENTO/NMAP.txt`):

```bash
Descripción:▶ Escaneo Rápido (Puertos abiertos rápidamente):
Comando: nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP -oG allPorts
```

## Capturas de pantalla

| Funcionalidad | Captura |
|---|---|
| **Entrada correcta** | ![Entrada correcta](https://i.imgur.com/H6NeYAn.png) |
| **Entrada errónea** | ![Entrada errónea](https://i.imgur.com/7jJQM7S.png) |
| **Categoría actual** | ![Categoría actual](https://i.imgur.com/8pSYSkR.png) |
| **Autocompletado** | ![Autocompletado](https://i.imgur.com/7aSifEC.png) |

### Demostración en video
[Ver demostración en video](https://i.imgur.com/OkKMFUy.mp4)

## Terminales compatibles

| Terminal | Estado | Notas |
|---|---|---|
| **Terminator** | ✅ Funciona perfectamente | Sin problemas conocidos |
| **GNOME Terminal** | ✅ Funciona perfectamente | Sin problemas conocidos |
| **Parrot Terminal** | ✅ Funciona perfectamente | Sin problemas conocidos |
| **Kitty** | ⚠️ Limitaciones | Problemas con `Ctrl + L` y renderizado de iconos |

> **Recomendación**: Para una experiencia óptima, usa Terminator, GNOME Terminal o Parrot Terminal.

## Distribuciones soportadas

- **Kali Linux**: Probado y completamente funcional.
- **Ubuntu/Debian**: Funcional, pero puede requerir instalación adicional de dependencias.
- **Otras**: No probado, pero debería funcionar en sistemas con Python 3.6+.

## Desinstalación

Para desinstalar completamente **searchCommand** y **gtfsearch**:

```bash
sudo ./kali-install.py
```

Selecciona `[4] Desinstalar searchCommand`. Esto elimina todos los archivos instalados, incluyendo gtfsearch.

## Problemas conocidos

| Problema | Descripción | Solución |
|---|---|---|
| **utilscommon faltante** | La herramienta no funciona sin este archivo | Asegúrate de incluirlo al instalar |
| **Kitty Terminal** | Problemas con `Ctrl + L` y renderizado | Usa otros terminales recomendados |
| **Actualización directa** | gtfsearch no está disponible tras actualizar | Realiza una instalación limpia |

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar searchCommand, sigue estos pasos:
1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m "Agrega nueva funcionalidad"`).
4. Envía un pull request.

## Créditos

- **Inspiración**: Basado en los `utilscommon` de **[S1R3N](https://github.com/OHDUDEOKNICE)**. ¡Gracias por la inspiración!
- **GTFOBins**: Integración local basada en el proyecto **[GTFOBins](https://gtfobins.github.io/)**.

## Autor

**Jordan aka SkyW4r33x**  
[GitHub](https://github.com/SkyW4r33x/searchCommand)

<div align="center"> <h2>🧠 H4PPY H4CK1NG</h2>
<div align="center"> <h2>Hecha con corazón, en un mundo de mierda.</h2>

![Hacking](https://img.shields.io/badge/Sigue-Hackeando-brightgreen.svg) ![Security](https://img.shields.io/badge/Mantente-Seguro-red.svg) ![Learning](https://img.shields.io/badge/Nunca_Parar_de-Aprender-blue.svg)

</div>
