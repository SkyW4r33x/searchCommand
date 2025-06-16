![Banner](https://i.imgur.com/NII8Wbr.jpeg)  
*Herramienta de búsqueda interactiva para comandos de pentesting en Linux.*

**searchCommand** es una herramienta escrita en Python diseñada para pentesters y entusiastas de la seguridad informática. Permite buscar y explorar comandos organizados por categorías y herramientas de manera interactiva, con autocompletado, resaltado de sintaxis y un diseño inspirado en Kali Linux. Ideal para aprender, consultar o ejecutar comandos rápidamente desde la terminal.

**Autor**: Jordan aka SkyW4r33x  
**Versión**: 0.1  

## Características

- **Interfaz interactiva**: Busca comandos con un prompt estilo Kali, con soporte para autocompletado (Tab) y atajos de teclado.
- **Categorías y herramientas**: Organiza comandos en categorías definidas en `utilscommon` para fácil acceso.
- **Resaltado de sintaxis**: Colorea comandos, parámetros y comentarios para mayor claridad.
- **Sugerencias**: Si no encuentras un comando, te sugiere opciones similares.
- **Personalizable**: Usa un archivo `utilscommon` para definir tus propios comandos y categorías.

## 📋 Requisitos

- **Sistema operativo**: Linux (no compatible con Windows).
- **Python**: 3.6 o superior (debe incluir `venv` y `pip`, normalmente instalados por defecto en Kali Linux).

*Nota*: No necesitas instalar ninguna librería manualmente. El instalador (`kali-install.py`) se encarga de todo, incluyendo sus propias dependencias, creando entornos virtuales automáticamente.

## 🚀 Instalación

### Prerrequisitos
Asegúrate de tener Python 3 con `venv` y `pip`. En Kali Linux, esto suele venir preinstalado. Si no, instala con:
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```
## Pasos
1. Clona el repositorio:
```bash
git clone https://github.com/SkyW4r33x/searchCommand.git
cd searchCommand
```
2. Ejecuta el instalador: El script `kali-install.py` configura un entorno virtual y instala todas las dependencias automáticamente, sin requerir instalaciones previas.

```bash
chmod +x kali-install.py # dando permiso de ejecución
sudo ./kali-install.py
```
* Selecciona `[1] Instalar searchCommand` en el menú.
* Asegúrate de que `searchCommand.py`, `requirements.txt` y `referencestuff/utilscommon` estén en el directorio actual antes de ejecutar el instalador.

3. Verifica la instalación: Una vez instalado, ejecuta:
```bash
searchCommand
```
Deberías ver el banner y el prompt interactivo.

# 🖥️ Uso
## Modo interactivo
Ejecuta `searchCommand` sin argumentos para entrar en el modo interactivo:
```bash
searchCommand
```
* Usa `Tab` para autocompletar categorías o herramientas.
* Escribe `help` para ver los comandos disponibles.
* Atajos de teclado:
    * `Ctrl + L`: Limpiar pantalla.
    * `Ctrl + T`: Listar herramientas.
    * `Ctrl + K`: Listar categorías.
    * `Ctrl + C`: Salir.
## Ejemplo de comandos internos
* `list tools` (o `lt`): Muestra todas las herramientas.
* `list categories` (o `lc`): Muestra todas las categorías.
* `setip <IP> `: Configurar $IP para comandos
* `seturl <URL>`: Configurar $URL para comandos.
* `exit` (o `q`): Sale del programa.
## Búsqueda directa
Busca un comando específico y sal:
```bash
searchCommand -q nmap
```
## ⚙️ Formato de `utilscommon`

La herramienta `utilscommon` ahora organiza los comandos en una estructura de carpetas dentro del directorio `~/referencestuff`. Cada categoría es una carpeta, y dentro de cada carpeta se encuentran archivos que representan las herramientas con sus respectivos comandos.

## Estructura de Archivos

- **Categorías**: Las categorías se definen como carpetas dentro de `~/referencestuff`. Por ejemplo, una categoría como "RECONOCIMIENTO" sería una carpeta llamada `RECONOCIMIENTO`.

- **Herramientas**: Dentro de cada carpeta de categoría, las herramientas se definen como archivos de texto. Cada archivo lleva el nombre de la herramienta (por ejemplo, `NMAP.txt`) y contiene una descripción del comando seguida del comando en sí.

### Formato de un archivo de herramienta

Cada archivo de herramienta debe seguir este formato:

```
Descripción:▶ [Descripción del comando]
Comando: [Comando completo]
```

**Ejemplo** (`~/referencestuff/RECONOCIMIENTO/NMAP.txt`):
```
Descripción:▶ Escaneo Rápido (Puertos abiertos rápidamente):
Comando: nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP -oG allPorts
```
## Notas Importantes

- **Ubicación**: Los archivos de herramientas deben estar dentro de sus respectivas carpetas de categorías en `~/referencestuff`.
- **Formato estricto**: Cada archivo de herramienta debe contener las líneas `Descripción:` y `Comando:` exactamente como se indica, con el texto correspondiente después de cada una.
- **Errores**: Si una carpeta de categoría o un archivo de herramienta no se encuentra, o si el formato no es correcto, la herramienta generará un error similar a:
  ```
  ⚠️ Error al leer el archivo: Archivo no encontrado en /home/usuario/referencestuff/[CATEGORÍA]/[HERRAMIENTA]
  ```
  Se está trabajando en mejorar la gestión de errores en futuras versiones.

## Ejemplo de Estructura

```
~/referencestuff/
├── RECONOCIMIENTO/
│   ├── NMAP.txt
│   └── OTRA_HERRAMIENTA.txt
├── EXPLOTACIÓN/
│   ├── METASPLOIT.txt
│   └── OTRA_HERRAMIENTA.txt
```

## 🖥️ Prompt de `searchCommand`

El prompt interactivo de **`searchCommand`** te guía con un sistema de **autocompletado** intuitivo y muestra en tiempo real la **categoría** o **herramienta** en la que estás navegando. A continuación, se detallan los diferentes escenarios de uso con ejemplos visuales:

| **Escenario**                | **Descripción**                                      | **Ejemplo Visual**                                                                 |
|------------------------------|-----------------------------------------------------|------------------------------------------------------------------------------------|
| **Entrada correcta**         | El usuario ingresa un comando válido.               | ![Entrada correcta](https://i.imgur.com/H6NeYAn.png)                              |
| **Entrada errónea**          | El usuario introduce un comando no reconocido.      | ![Entrada errónea](https://i.imgur.com/7jJQM7S.png)                               |
| **Categoría o herramienta actual** | Muestra el contexto actual de navegación.          | ![Categoría actual](https://i.imgur.com/8pSYSkR.png)                              |
| **Visualización del autocompletado** | Sugerencias dinámicas mientras escribes.          | ![enter image description here](https://i.imgur.com/7aSifEC.png)     |

[Ver demostración en video](https://i.imgur.com/OkKMFUy.mp4)


## 🗑️ Desinstalación
### Para desinstalar:
```bash
sudo ./kali-install.py
```
Selecciona `[2] Desinstalar searchCommand`. Esto elimina todos los archivos instalados.

## Terminales Probadas
La herramienta ha sido probada en las siguientes terminales en entornos Linux:
## ✅ Terminales Probadas  

| Terminal        | Estado                                              |
|-----------------|-----------------------------------------------------|
| Kitty           | Funciona con limitaciones: problemas al limpiar pantalla con Ctrl + L (el historial reaparece al desplazar hacia arriba) y renderizado parcial de íconos. |
| Terminator      | Funciona correctamente sin problemas conocidos      |
| GNOME Terminal  | Funciona correctamente sin problemas conocidos      |
| Parrot Terminal | Funciona correctamente sin problemas conocidos      |

**Nota**: En Kitty, `Ctrl + L` limpia la pantalla, pero el historial reaparece al desplazar hacia arriba.
Si usas Kitty y encuentras este problema, considera usar Terminator, GNOME Terminal o en caso si estas en Parrot usar Parrot Terminal para una experiencia más fluida.

## ⚠️ Problemas conocidos
* Si utilscommon no está presente o tiene un formato incorrecto, la herramienta no funcionará. Asegúrate de incluirlo al instalar.
* En Kitty, limpiar la pantalla tiene el problema descrito arriba. Otros emuladores podrían mostrar colores o formato inconsistente.

📌 Esta herramienta está inspirada en los  `utilscommon` de **[S1R3N](https://github.com/OHDUDEOKNICE)** los cuales consistían principalmente en apuntes accesibles desde la terminal mediante alias. A partir de ahí, fue modificada y optimizada, incorporando una útil función de búsqueda de comandos para facilitar su uso y mejorar la experiencia general.

# **H4PPY H4CK1NG**
