# searchCommand

![Banner](https://i.imgur.com/NII8Wbr.jpeg)  
*Herramienta de búsqueda interactiva para comandos de pentesting en Linux.*

**searchCommand** es una herramienta escrita en Python diseñada para pentesters y entusiastas de la seguridad informática. Permite buscar y explorar comandos organizados por categorías y herramientas de manera interactiva, con autocompletado, resaltado de sintaxis y un diseño inspirado en Kali Linux. Ideal para aprender, consultar o ejecutar comandos rápidamente desde la terminal.

**Autor**: Jordan aka SkyW4r33x  
**Versión**: 0.1  
**Repositorio**: [https://github.com/SkyW4r33x/](https://github.com/SkyW4r33x/searchCommand)

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
* `clear` (o `c`): Limpia la pantalla.
* `exit` (o `q`): Sale del programa.
## Búsqueda directa
Busca un comando específico y sal:
```bash
searchCommand -q nmap
```
## ⚙️ Formato de `utilscommon`
La herramienta lee comandos desde `~/referencestuff/utilscommon`. Este archivo debe tener un formato específico:
```bash
[+]------------------------------[ RECONOCIMIENTO ]------------------------------[+]
[*] NMAP
▶ Escaneo completo:
   nmap -p- -sS -sV -A $IP -oN targeted  
```
* `[+]---[ ]---[+]`: Define una categoría.
* `[*]`: Define una herramienta dentro de la categoría.
* `▶`: Descripción del comando y abajo de ello el comando entero.

**NOTA**: Si falta este archivo o está mal formateado, la herramienta fallará con un error, se trata de corregir este problema en las nuevas versiones:
```bash
⚠️ Error al leer el archivo: Archivo no encontrado en /home/usuario/referencestuff/utilscommon
```
## 🖥️ Prompt de `searchCommand`

El prompt interactivo de **`searchCommand`** te guía con un sistema de **autocompletado** intuitivo y muestra en tiempo real la **categoría** o **herramienta** en la que estás navegando. A continuación, se detallan los diferentes escenarios de uso con ejemplos visuales:

| **Escenario**                | **Descripción**                                      | **Ejemplo Visual**                                                                 |
|------------------------------|-----------------------------------------------------|------------------------------------------------------------------------------------|
| **Entrada correcta**         | El usuario ingresa un comando válido.               | ![Entrada correcta](https://i.imgur.com/H6NeYAn.png)                              |
| **Entrada errónea**          | El usuario introduce un comando no reconocido.      | ![Entrada errónea](https://i.imgur.com/7jJQM7S.png)                               |
| **Categoría o herramienta actual** | Muestra el contexto actual de navegación.          | ![Categoría actual](https://i.imgur.com/8pSYSkR.png)                              |
| **Visualización del autocompletado** | Sugerencias dinámicas mientras escribes.          | ![enter image description here](https://i.imgur.com/7aSifEC.png)     |

🎥 [Ver demostración en video](https://i.imgur.com/OkKMFUy.mp4)


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