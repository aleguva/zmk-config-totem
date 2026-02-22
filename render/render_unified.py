#!/usr/bin/env python3
"""
Genera layout unificado del TOTEM con todas las capas visibles en una sola imagen.
BASE en el centro (grande), otras capas alrededor (pequeñas), todo con rotación.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# === CONFIGURACIÓN ===
REPO_ROOT = Path(__file__).parent.parent
KEYMAP_FILE = REPO_ROOT / "config" / "totem.keymap"
SVG_TEMPLATE = REPO_ROOT / "docs" / "images" / "TOTEM_layout_template.svg"
OUTPUT_SVG = REPO_ROOT / "docs" / "images" / "TOTEM_layout.svg"
OUTPUT_PNG = REPO_ROOT / "docs" / "images" / "TOTEM_layout.png"
BACKUP_SVG = REPO_ROOT / "docs" / "images" / "TOTEM_layout_backup.svg"

TOTAL_KEYS = 38

# Capas a mostrar según mitad del teclado
# LEFT = teclas k00-k04, k10-k14, k20-k24, k30-k32, k36
# RIGHT = teclas k05-k09, k15-k19, k25-k29, k33-k35, k37

LEFT_LAYERS = {
    "BASE": {"position": "top-left", "color": "#58a6ff", "font_size": 12},
    "SYM": {"position": "top-right", "color": "#ffa657", "font_size": 8},
    "FUN": {"position": "bottom-left", "color": "#d2a8ff", "font_size": 8},
    "NUM": {"position": "bottom-right", "color": "#f0883e", "font_size": 8},
}

RIGHT_LAYERS = {
    "BASE": {"position": "top-left", "color": "#58a6ff", "font_size": 12},
    "MOUSE": {"position": "top-right", "color": "#a5d6ff", "font_size": 8},
    "MEDIA": {"position": "bottom-left", "color": "#f778ba", "font_size": 8},
    "NAV": {"position": "bottom-right", "color": "#79c0ff", "font_size": 8},
}

# Offsets para posicionar texto en las esquinas de cada tecla
POSITION_OFFSETS = {
    "top-left": (-14, -10),
    "top-right": (14, -10),
    "bottom-left": (-14, 10),
    "bottom-right": (14, 10),
}

# Teclas de la mitad izquierda (índices)
# Fila 1: k00-k04 (Q W F P B)
# Fila 2: k10-k14 (A R S T G)
# Fila 3: k20-k24 (Z X C D V) + k36 (outer pinkie izq)
# Thumbs: k30-k32 (ESC SPACE TAB)
LEFT_KEYS = {0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 30, 31, 32, 36}
# Fila 3 derecha: k25-k29 (K H , . /) + k37 (outer pinkie der)
# Thumbs derecha: k33-k35 (RET BSPC DEL)

# Teclas que necesitan rotación adicional de 90º (borde derecho vertical)
# k08=Y, k09=', k18=I, k19=O, k28=,, k29=., k37=thumb derecho exterior
KEYS_NEED_90_ROTATION = {8, 9, 18, 19, 28, 29, 37}

# Padding alrededor del SVG (en px)
SVG_PADDING = 20

# Configuración del rectángulo de profundidad
DEPTH_SCALE = 0.85  # Porcentaje del tamaño original (85%)
DEPTH_OFFSET_X = 1.5  # Desplazamiento horizontal
DEPTH_OFFSET_Y = 1.5  # Desplazamiento vertical

@dataclass
class KeyInfo:
    """Información de geometría de una tecla"""
    id: str
    x: float
    y: float
    width: float
    height: float
    rotation: Optional[float] = None  # en grados
    rotation_cx: Optional[float] = None  # centro de rotación X
    rotation_cy: Optional[float] = None  # centro de rotación Y

# === PARSER DE KEYMAP (simplificado del original) ===

def clean_token(token: str) -> str:
    """Convierte tokens ZMK a etiquetas legibles"""
    token = token.strip()

    if token in ("&trans",):
        return ""

    # Casos especiales
    replacements = {
        "COMMA": ",", "DOT": ".", "FSLH": "/", "BSLH": "\\", "SQT": "'",
        "SEMI": ";", "LBKT": "[", "RBKT": "]", "LBRC": "{", "RBRC": "}",
        "LPAR": "(", "RPAR": ")", "MINUS": "-", "EQUAL": "=", "GRAVE": "`",
        "BSPC": "⌫", "RET": "↵", "SPACE": "␣", "TAB": "⇥", "ESC": "⎋",
        "DEL": "⌦", "CAPS": "⇪", "LSHFT": "⇧", "RSHFT": "⇧",
        "LCTRL": "⌃", "RCTRL": "⌃", "LALT": "⌥", "RALT": "⌥",
        "LGUI": "⌘", "RGUI": "⌘", "LEFT": "←", "DOWN": "↓", "UP": "↑", "RIGHT": "→",
        "PG_DN": "PgDn", "PG_UP": "PgUp", "HOME": "Home", "END": "End",
        "INS": "Ins", "PSCRN": "PrtSc", "SLCK": "ScrLk", "PAUSE_BREAK": "Pause",
        # Símbolos especiales
        "AMPS": "&", "STAR": "*", "CARET": "^",
        "DLLR": "$", "PRCNT": "%", "PLUS": "+",
        "COLON": ":", "TILDE": "~", "EXCL": "!",
        "AT": "@", "HASH": "#", "PIPE": "|", "UNDER": "_",
    }

    # Combinaciones macOS y teclas con &kp
    if token.startswith("&kp "):
        key = token.replace("&kp ", "")
        if "LG(" in key:
            if "LG(LS(" in key:  # Cmd+Shift+Z
                inner = key.replace("LG(LS(", "").replace("))", "")
                return f"⌘⇧{inner}"
            else:  # Cmd+C, etc.
                inner = key.replace("LG(", "").replace(")", "")
                return f"⌘{inner}"
        # Números: N7 -> 7
        if key.startswith("N") and key[1:].isdigit():
            return key[1:]
        return replacements.get(key, key)

    # Home row mods: &mt LGUI A → A (sin mostrar mod en compacto)
    if token.startswith("&mt "):
        parts = token.split()
        return parts[-1] if len(parts) >= 3 else token

    # Layer taps: &lt NAV TAB → TAB (solo la tecla)
    if token.startswith("&lt "):
        parts = token.split()
        key = parts[-1] if len(parts) >= 3 else token
        return replacements.get(key, key)

    # &mo BUTTON → BTN
    if token.startswith("&mo "):
        return ""  # No mostrar layer momentary en compacto

    # Mouse buttons
    if token.startswith("&mkp "):
        btn = token.replace("&mkp ", "")
        return {"LCLK": "ML", "RCLK": "MR", "MCLK": "MM"}.get(btn, btn)

    # Bluetooth
    if "&bt " in token or "BT_SEL" in token:
        parts = token.split()
        for i, part in enumerate(parts):
            if "BT_SEL" in part and i + 1 < len(parts):
                return f"BT{parts[i + 1]}"
        return "BT"

    # Out toggle
    if "OUT_TOG" in token:
        return "OUT"

    # Media keys
    if token.startswith("&kp C_"):
        media = token.replace("&kp C_", "")
        media_map = {
            "PREV": "⏮", "NEXT": "⏭", "PP": "⏯", "STOP": "⏹",
            "VOL_DN": "🔉", "VOL_UP": "🔊", "MUTE": "🔇",
            "BRI_DN": "🔅", "BRI_UP": "🔆",
        }
        return media_map.get(media, media)

    # Function keys
    if token.startswith("&kp F") and token[4:].replace("&kp ", "").isdigit():
        return token.replace("&kp ", "")

    # Números (extraer solo el dígito)
    if token.startswith("&kp N") and len(token) > 5:
        return token.replace("&kp N", "")

    # Fallback - limpiar prefijos
    clean = token.replace("&", "").replace("kp ", "")

    # Si después de limpiar queda algo como "N7", "N0", etc, extraer solo el número
    if clean.startswith("N") and len(clean) >= 2 and clean[1:].isdigit():
        return clean[1:]

    return clean


def parse_layers(text: str) -> Dict[str, List[str]]:
    """Parsea capas del keymap"""
    layers = {}
    pattern = re.compile(r'(\w+)_layer\s*{.*?bindings\s*=\s*<([^>]+)>;', re.S)

    for layer_name, bindings_block in pattern.findall(text):
        # Limpiar comentarios
        lines = bindings_block.split('\n')
        clean_lines = []
        for line in lines:
            if '//' in line:
                line = line[:line.index('//')]
            clean_lines.append(line)

        clean_text = ' '.join(clean_lines).replace('╷', '')
        tokens = [t.strip() for t in clean_text.split() if t.strip()]

        keys = []
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Detectar combinaciones multi-token
            if token in ("&mt", "&lt"):
                if i + 2 < len(tokens):
                    combined = " ".join(tokens[i:i+3])
                    keys.append(clean_token(combined))
                    i += 3
                else:
                    keys.append(clean_token(token))
                    i += 1
            elif token in ("&bt",):
                if i + 2 < len(tokens):
                    combined = " ".join(tokens[i:i+3])
                    keys.append(clean_token(combined))
                    i += 3
                else:
                    keys.append(clean_token(token))
                    i += 1
            elif token in ("&out", "&mmv", "&msc"):
                if i + 1 < len(tokens):
                    combined = " ".join(tokens[i:i+2])
                    keys.append(clean_token(combined))
                    i += 2
                else:
                    keys.append(clean_token(token))
                    i += 1
            elif token in ("&kp", "&mkp", "&mo"):
                if i + 1 < len(tokens):
                    combined = " ".join(tokens[i:i+2])
                    keys.append(clean_token(combined))
                    i += 2
                else:
                    keys.append(clean_token(token))
                    i += 1
            else:
                keys.append(clean_token(token))
                i += 1

        if len(keys) == TOTAL_KEYS:
            layers[layer_name.upper()] = keys

    return layers


# === EXTRACCIÓN DE GEOMETRÍA DEL SVG ===

def parse_key_geometry(svg_file: Path) -> Dict[str, KeyInfo]:
    """Extrae geometría y rotación de cada tecla del SVG"""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    keys_info = {}

    for rect in root.findall(".//svg:rect[@id]", ns):
        key_id = rect.attrib.get('id', '')
        if not key_id.startswith('k'):
            continue

        x = float(rect.attrib.get('x', 0))
        y = float(rect.attrib.get('y', 0))
        width = float(rect.attrib.get('width', 49.61))
        height = float(rect.attrib.get('height', 46.77))

        # Extraer rotación del transform
        transform = rect.attrib.get('transform', '')
        rotation = None
        rotation_cx = None
        rotation_cy = None

        if 'rotate' in transform:
            # Formato: rotate(-10 67.2 97.7)
            match = re.search(r'rotate\(([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)', transform)
            if match:
                rotation = float(match.group(1))
                rotation_cx = float(match.group(2))
                rotation_cy = float(match.group(3))

        keys_info[key_id] = KeyInfo(
            id=key_id,
            x=x,
            y=y,
            width=width,
            height=height,
            rotation=rotation,
            rotation_cx=rotation_cx,
            rotation_cy=rotation_cy
        )

    return keys_info


# === GENERACIÓN DE SVG UNIFICADO ===

def generate_unified_svg(layers: Dict[str, List[str]], keys_info: Dict[str, KeyInfo], output_file: Path):
    """Genera SVG con todas las capas superpuestas en cada tecla"""

    # Calcular viewBox con padding
    vb_x = -SVG_PADDING
    vb_y = -SVG_PADDING
    vb_width = 733.16 + (SVG_PADDING * 2)
    vb_height = 267.46 + (SVG_PADDING * 2)

    # Inicio del SVG
    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="{vb_width}" height="{vb_height}"',
        f'     viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">',
        '',
        '  <defs>',
        '    <style>',
        '      .cls-bg { fill: #0d1117; }',
        '      .cls-depth {',
        '        fill: #0d1117;',
        '        stroke: #30363d;',
        '        stroke-width: 0.4px;',
        '      }',
        '      .cls-key {',
        '        fill: #1f2630;',
        '        stroke: #58a6ff;',
        '        stroke-width: 0.6px;',
        '        stroke-miterlimit: 10;',
        '      }',
        '      text {',
        '        font-family: monospace;',
        '        text-anchor: middle;',
        '        dominant-baseline: middle;',
        '      }',
        '    </style>',
        '  </defs>',
        '',
        '  <!-- Fondo con reborde -->',
        f'  <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" class="cls-bg"/>',
        '',
        '  <g id="unified-layout">',
    ]

    # Leer template para copiar los rectángulos originales
    tree = ET.parse(SVG_TEMPLATE)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    # Primero, copiar rectángulos de profundidad (sombra)
    svg_parts.append('    <!-- Rectángulos de profundidad -->')
    for i in range(TOTAL_KEYS):
        key_id = f"k{i:02d}"
        rect = root.find(f".//svg:rect[@id='{key_id}']", ns)

        if rect is not None and key_id in keys_info:
            key_info = keys_info[key_id]
            depth_attrs = rect.attrib.copy()

            # Obtener dimensiones originales
            orig_x = float(depth_attrs['x'])
            orig_y = float(depth_attrs['y'])
            orig_width = float(depth_attrs['width'])
            orig_height = float(depth_attrs['height'])

            # Calcular nuevas dimensiones (más pequeñas)
            new_width = orig_width * DEPTH_SCALE
            new_height = orig_height * DEPTH_SCALE

            # Centrar y aplicar offset
            new_x = orig_x + (orig_width - new_width) / 2 + DEPTH_OFFSET_X
            new_y = orig_y + (orig_height - new_height) / 2 + DEPTH_OFFSET_Y

            # Actualizar atributos
            depth_attrs['x'] = str(new_x)
            depth_attrs['y'] = str(new_y)
            depth_attrs['width'] = str(new_width)
            depth_attrs['height'] = str(new_height)
            depth_attrs['class'] = 'cls-depth'
            depth_attrs['id'] = f"{key_id}-depth"

            attr_str = ' '.join(f'{k}="{v}"' for k, v in depth_attrs.items())
            svg_parts.append(f'    <rect {attr_str}/>')

    # Luego, copiar rectángulos de teclas principales
    svg_parts.append('    <!-- Teclas principales -->')
    for i in range(TOTAL_KEYS):
        key_id = f"k{i:02d}"
        rect = root.find(f".//svg:rect[@id='{key_id}']", ns)

        if rect is not None:
            rect_attrs = rect.attrib.copy()
            rect_attrs['class'] = 'cls-key'
            attr_str = ' '.join(f'{k}="{v}"' for k, v in rect_attrs.items())
            svg_parts.append(f'    <rect {attr_str}/>')

    # Añadir textos de todas las capas visibles
    svg_parts.append('    <!-- Textos de capas -->')
    for i in range(TOTAL_KEYS):
        key_id = f"k{i:02d}"

        if key_id not in keys_info:
            continue

        key_info = keys_info[key_id]

        # Centro de la tecla (antes de rotación)
        cx = key_info.x + key_info.width / 2
        cy = key_info.y + key_info.height / 2

        # Determinar si es tecla izquierda o derecha
        is_left = i in LEFT_KEYS
        layers_config = LEFT_LAYERS if is_left else RIGHT_LAYERS

        # Añadir texto de cada capa visible
        for layer_name, layer_config in layers_config.items():
            if layer_name not in layers:
                continue

            label = layers[layer_name][i]
            if not label:  # Saltar &trans
                continue

            position = layer_config["position"]
            color = layer_config["color"]
            font_size = layer_config["font_size"]

            # Calcular offset
            offset_x, offset_y = POSITION_OFFSETS[position]
            text_x = cx + offset_x
            text_y = cy + offset_y

            # Construir transform con rotación si existe
            transform_str = ""
            if key_info.rotation is not None:
                # Ajustar rotación para teclas verticales del borde derecho
                text_rotation = key_info.rotation
                if i in KEYS_NEED_90_ROTATION:
                    text_rotation = text_rotation + 90
                transform_str = f' transform="rotate({text_rotation} {key_info.rotation_cx} {key_info.rotation_cy})"'

            # Escapar caracteres XML
            label_escaped = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Generar elemento de texto
            svg_parts.append(
                f'    <text x="{text_x}" y="{text_y}" '
                f'fill="{color}" font-size="{font_size}"{transform_str}>{label_escaped}</text>'
            )

    # Cerrar SVG
    svg_parts.append('  </g>')
    svg_parts.append('</svg>')

    # Escribir archivo
    output_file.write_text('\n'.join(svg_parts), encoding='utf-8')
    print(f"✅ SVG unificado generado: {output_file}")


# === MAIN ===

def main():
    import subprocess
    import shutil

    print("🔍 Leyendo keymap...")
    keymap_text = KEYMAP_FILE.read_text(encoding='utf-8')

    print("🔧 Parseando capas...")
    layers = parse_layers(keymap_text)

    # Filtrar solo capas necesarias (union de LEFT y RIGHT)
    all_layer_names = set(LEFT_LAYERS.keys()) | set(RIGHT_LAYERS.keys())
    filtered_layers = {k: v for k, v in layers.items() if k in all_layer_names}

    print(f"📊 Capas a renderizar: {', '.join(sorted(filtered_layers.keys()))}")
    for layer_name in sorted(all_layer_names):
        if layer_name in filtered_layers:
            keys = filtered_layers[layer_name]
            non_empty = sum(1 for k in keys if k)
            print(f"   • {layer_name}: {non_empty}/38 teclas definidas")

    print("\n🔑 Extrayendo geometría de teclas...")
    keys_info = parse_key_geometry(SVG_TEMPLATE)
    print(f"   ✅ {len(keys_info)} teclas encontradas")

    # Backup del SVG anterior si existe
    if OUTPUT_SVG.exists():
        print(f"\n💾 Creando backup: {BACKUP_SVG}")
        shutil.copy(OUTPUT_SVG, BACKUP_SVG)

    print("\n🎨 Generando SVG unificado...")
    generate_unified_svg(filtered_layers, keys_info, OUTPUT_SVG)

    # Exportar a PNG
    print("\n🖼️  Exportando a PNG...")
    try:
        subprocess.run(
            ["rsvg-convert", "-w", "2000", str(OUTPUT_SVG), "-o", str(OUTPUT_PNG)],
            check=True,
            capture_output=True
        )
        print(f"   ✅ PNG generado: {OUTPUT_PNG}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"   ⚠️  Error al generar PNG: {e}")
        print(f"   💡 Instala librsvg: brew install librsvg")

    print(f"\n✨ Proceso completado!")
    print(f"   📄 SVG: {OUTPUT_SVG}")
    print(f"   🖼️  PNG: {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
