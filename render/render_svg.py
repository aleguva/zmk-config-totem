#!/usr/bin/env python3
"""
Genera automáticamente TOTEM_layout.svg con todas las capas del keymap
coloreadas por capa, basándose en totem.keymap
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

# === CONFIGURACIÓN ===
REPO_ROOT = Path(__file__).parent.parent
KEYMAP_FILE = REPO_ROOT / "config" / "totem.keymap"
SVG_TEMPLATE = REPO_ROOT / "docs" / "images" / "TOTEM_layout.svg"
OUTPUT_SVG = REPO_ROOT / "docs" / "images" / "TOTEM_layout.svg"
OUTPUT_PNG = REPO_ROOT / "docs" / "images" / "TOTEM_layout.png"
BACKUP_SVG = REPO_ROOT / "docs" / "images" / "TOTEM_layout_old.svg"

TOTAL_KEYS = 38
LAYER_HEIGHT = 300  # Espacio vertical entre capas en el SVG final

# Colores por capa (tema oscuro GitHub-like)
LAYER_COLORS = {
    "BASE": "#58a6ff",    # Azul claro
    "NAV": "#79c0ff",     # Azul cielo
    "MOUSE": "#a5d6ff",   # Azul pastel
    "MEDIA": "#f778ba",   # Rosa
    "SYM": "#ffa657",     # Naranja
    "NUM": "#f0883e",     # Naranja oscuro
    "FUN": "#d2a8ff",     # Púrpura
    "BUTTON": "#56d364",  # Verde
}

# === PARSER (basado en parse_totem_keymap.py) ===

def clean_token(token: str) -> str:
    """Convierte tokens ZMK a etiquetas legibles"""
    token = token.strip()

    if token in ("&trans",):
        return ""

    # Casos especiales de limpieza
    replacements = {
        "COMMA": ",",
        "DOT": ".",
        "FSLH": "/",
        "BSLH": "\\",
        "SQT": "'",
        "SEMI": ";",
        "LBKT": "[",
        "RBKT": "]",
        "LBRC": "{",
        "RBRC": "}",
        "LPAR": "(",
        "RPAR": ")",
        "MINUS": "-",
        "EQUAL": "=",
        "GRAVE": "`",
        "BSPC": "⌫",
        "RET": "↵",
        "SPACE": "␣",
        "TAB": "⇥",
        "ESC": "⎋",
        "DEL": "⌦",
        "CAPS": "⇪",
        "LSHFT": "⇧",
        "RSHFT": "⇧",
        "LCTRL": "⌃",
        "RCTRL": "⌃",
        "LALT": "⌥",
        "RALT": "⌥",
        "LGUI": "⌘",
        "RGUI": "⌘",
        "LEFT": "←",
        "DOWN": "↓",
        "UP": "↑",
        "RIGHT": "→",
        "PG_DN": "PgDn",
        "PG_UP": "PgUp",
        "HOME": "Home",
        "END": "End",
        "INS": "Ins",
        "PSCRN": "PrtSc",
        "SLCK": "ScrLk",
        "PAUSE_BREAK": "Pause",
    }

    # &kp Q, &kp COMMA, etc.
    if token.startswith("&kp "):
        key = token.replace("&kp ", "")
        # Detectar combinaciones de macOS (Cmd+C, etc.)
        if "LG(" in key:
            # Extraer la combinación
            if "LG(LS(" in key:  # Cmd+Shift+Z
                inner = key.replace("LG(LS(", "").replace("))", "")
                return f"⌘⇧{inner}"
            elif "LG(" in key:  # Cmd+C, Cmd+V, etc.
                inner = key.replace("LG(", "").replace(")", "")
                return f"⌘{inner}"
        return replacements.get(key, key)

    # &mt LGUI A → A (con mod)
    if token.startswith("&mt "):
        parts = token.split()
        if len(parts) >= 3:
            mod = parts[1].replace("L", "").replace("R", "")[:1]
            key = parts[2]
            return f"{key}\n{mod}"
        return token.split()[-1]

    # &lt NAV TAB → TAB↓NAV
    if token.startswith("&lt "):
        parts = token.split()
        if len(parts) >= 3:
            layer = parts[1][:3]
            key = parts[2]
            key_display = replacements.get(key, key)
            return f"{key_display}\n↓{layer}"
        return token.split()[-1]

    # &mo BUTTON → ⇓BTN
    if token.startswith("&mo "):
        layer = token.split()[1][:3]
        return f"⇓{layer}"

    # Mouse movement
    if "MOVE_" in token:
        direction = token.split("_")[-1][:1]
        return f"M{direction}"

    # Mouse scroll
    if "SCRL_" in token:
        direction = token.split("_")[-1][:1]
        return f"S{direction}"

    # Mouse buttons
    if token.startswith("&mkp "):
        btn = token.replace("&mkp ", "")
        btn_map = {"LCLK": "L", "RCLK": "R", "MCLK": "M"}
        return f"M{btn_map.get(btn, btn)}"

    # Bluetooth - formato: "&bt BT_SEL 0"
    if "&bt " in token or "BT_SEL" in token:
        parts = token.split()
        # Buscar el número después de BT_SEL
        for i, part in enumerate(parts):
            if "BT_SEL" in part and i + 1 < len(parts):
                return f"BT{parts[i + 1]}"
        # Si no encontramos número, mostrar solo BT
        return "BT"

    # Out toggle
    if "OUT_TOG" in token or "&out " in token:
        return "OUT"

    # Media keys
    if token.startswith("&kp C_"):
        media = token.replace("&kp C_", "")
        media_map = {
            "PREV": "⏮",
            "NEXT": "⏭",
            "PP": "⏯",
            "STOP": "⏹",
            "VOL_DN": "🔉",
            "VOL_UP": "🔊",
            "MUTE": "🔇",
            "BRI_DN": "🔅",
            "BRI_UP": "🔆",
        }
        return media_map.get(media, media)

    # Function keys
    if token.startswith("&kp F") and token[4:].replace("&kp ", "").isdigit():
        return token.replace("&kp ", "")

    # Números
    if token.startswith("&kp N"):
        return token.replace("&kp N", "")

    # Símbolos especiales
    symbol_map = {
        "&kp AMPS": "&",
        "&kp STAR": "*",
        "&kp CARET": "^",
        "&kp DLLR": "$",
        "&kp PRCNT": "%",
        "&kp PLUS": "+",
        "&kp COLON": ":",
        "&kp TILDE": "~",
        "&kp EXCL": "!",
        "&kp AT": "@",
        "&kp HASH": "#",
        "&kp PIPE": "|",
        "&kp UNDER": "_",
    }
    if token in symbol_map:
        return symbol_map[token]

    # Fallback
    return token.replace("&", "").replace("kp ", "")


def parse_layers(text: str) -> Dict[str, List[str]]:
    """Parsea todas las capas del keymap"""
    layers = {}

    pattern = re.compile(
        r'(\w+)_layer\s*{.*?bindings\s*=\s*<([^>]+)>;',
        re.S
    )

    for layer_name, bindings_block in pattern.findall(text):
        # Limpiar el bloque de bindings
        # Eliminar líneas con comentarios completas
        lines = bindings_block.split('\n')
        clean_lines = []
        for line in lines:
            # Eliminar comentarios al final de línea
            if '//' in line:
                line = line[:line.index('//')]
            clean_lines.append(line)

        clean_text = ' '.join(clean_lines)

        # Eliminar caracteres de decoración
        clean_text = clean_text.replace('╷', '')

        # Separar tokens y filtrar vacíos
        tokens = [t.strip() for t in clean_text.split() if t.strip() and t.strip() != '╷']

        keys = []
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Detectar combinaciones que necesitan múltiples tokens
            if token in ("&mt", "&lt"):
                if i + 2 < len(tokens):
                    combined = " ".join(tokens[i:i+3])
                    keys.append(clean_token(combined))
                    i += 3
                else:
                    keys.append(clean_token(token))
                    i += 1
            # Comandos especiales de Bluetooth (necesitan 2 tokens: &bt BT_SEL + número)
            elif token in ("&bt",):
                if i + 2 < len(tokens):
                    combined = " ".join(tokens[i:i+3])
                    keys.append(clean_token(combined))
                    i += 3
                else:
                    keys.append(clean_token(token))
                    i += 1
            # Out toggle
            elif token in ("&out",):
                if i + 1 < len(tokens):
                    combined = " ".join(tokens[i:i+2])
                    keys.append(clean_token(combined))
                    i += 2
                else:
                    keys.append(clean_token(token))
                    i += 1
            # Movimiento de mouse
            elif token in ("&mmv", "&msc"):
                if i + 1 < len(tokens):
                    combined = " ".join(tokens[i:i+2])
                    keys.append(clean_token(combined))
                    i += 2
                else:
                    keys.append(clean_token(token))
                    i += 1
            # &kp necesita combinar con el siguiente token
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

        # Validación
        if len(keys) != TOTAL_KEYS:
            print(f"⚠️  Capa {layer_name} tiene {len(keys)} teclas (esperadas {TOTAL_KEYS})")
            print(f"   Teclas encontradas: {keys}")
            continue

        layers[layer_name.upper()] = keys

    return layers


# === GENERADOR DE SVG ===

def create_layer_svg(layer_name: str, keys: List[str], y_offset: float) -> str:
    """Crea el SVG de una capa individual"""
    color = LAYER_COLORS.get(layer_name, "#ffffff")

    svg_parts = [
        f'  <!-- {layer_name} LAYER -->',
        f'  <g id="layer-{layer_name}" transform="translate(0, {y_offset})">',
        f'    <text x="20" y="20" fill="{color}" font-size="18" font-weight="bold">{layer_name}</text>',
    ]

    # Cargar template para obtener posiciones de teclas
    tree = ET.parse(SVG_TEMPLATE)
    root = tree.getroot()

    # Namespace para SVG
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    # Copiar teclas y añadir texto
    for i, key_label in enumerate(keys):
        key_id = f"k{i:02d}"

        # Buscar el rectángulo original
        rect = root.find(f".//svg:rect[@id='{key_id}']", ns)
        if rect is None:
            continue

        # Copiar atributos del rectángulo
        rect_attrs = rect.attrib.copy()
        rect_attrs['id'] = f"{layer_name}-{key_id}"
        rect_attrs['class'] = 'cls-2'
        rect_attrs['stroke'] = color

        # Crear elemento rect
        attr_str = ' '.join(f'{k}="{v}"' for k, v in rect_attrs.items())
        svg_parts.append(f'    <rect {attr_str}/>')

        # Añadir texto si la tecla no está vacía
        if key_label:
            # Obtener centro de la tecla (aproximado)
            x = float(rect_attrs.get('x', 0))
            y = float(rect_attrs.get('y', 0))
            width = float(rect_attrs.get('width', 49.61))
            height = float(rect_attrs.get('height', 46.77))

            # Centro de la tecla
            cx = x + width / 2
            cy = y + height / 2

            # Si hay salto de línea (ej: "A\nG"), dividir en dos líneas
            if '\n' in key_label:
                lines = key_label.split('\n')
                svg_parts.append(
                    f'    <text x="{cx}" y="{cy - 5}" fill="#c9d1d9" '
                    f'font-size="11" text-anchor="middle" font-family="monospace">{lines[0]}</text>'
                )
                svg_parts.append(
                    f'    <text x="{cx}" y="{cy + 9}" fill="#8b949e" '
                    f'font-size="8" text-anchor="middle" font-family="monospace">{lines[1]}</text>'
                )
            else:
                # Ajustar tamaño de fuente según longitud
                font_size = 10 if len(key_label) > 3 else 12
                svg_parts.append(
                    f'    <text x="{cx}" y="{cy + 4}" fill="#c9d1d9" '
                    f'font-size="{font_size}" text-anchor="middle" font-family="monospace">{key_label}</text>'
                )

    svg_parts.append('  </g>')
    return '\n'.join(svg_parts)


def generate_svg(layers: Dict[str, List[str]], output_file: Path):
    """Genera el SVG completo con todas las capas"""

    # Calcular altura total
    num_layers = len(layers)
    total_height = num_layers * LAYER_HEIGHT

    # Inicio del SVG
    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg"',
        f'     width="733.16" height="{total_height}"',
        f'     viewBox="0 0 733.16 {total_height}">',
        '',
        '  <defs>',
        '    <style>',
        '      .cls-1 { fill: #161b22; }',
        '      .cls-2 {',
        '        fill: #1f2630;',
        '        stroke-width: 0.6px;',
        '        stroke-miterlimit: 10;',
        '      }',
        '    </style>',
        '  </defs>',
        '',
    ]

    # Generar cada capa
    layer_order = ["BASE", "NAV", "MOUSE", "MEDIA", "SYM", "NUM", "FUN", "BUTTON"]
    for idx, layer_name in enumerate(layer_order):
        if layer_name in layers:
            y_offset = idx * LAYER_HEIGHT
            layer_svg = create_layer_svg(layer_name, layers[layer_name], y_offset)
            svg_parts.append(layer_svg)
            svg_parts.append('')

    # Cierre del SVG
    svg_parts.append('</svg>')

    # Escribir archivo
    output_file.write_text('\n'.join(svg_parts), encoding='utf-8')
    print(f"✅ SVG generado: {output_file}")


# === MAIN ===

def main():
    import subprocess
    import shutil

    print("🔍 Leyendo keymap...")
    keymap_text = KEYMAP_FILE.read_text(encoding='utf-8')

    print("🔧 Parseando capas...")
    layers = parse_layers(keymap_text)

    print(f"📊 Capas encontradas: {', '.join(layers.keys())}")
    for layer_name, keys in layers.items():
        non_empty = sum(1 for k in keys if k)
        print(f"   • {layer_name}: {non_empty}/38 teclas definidas")

    # Backup del SVG anterior si existe
    if OUTPUT_SVG.exists() and OUTPUT_SVG != SVG_TEMPLATE:
        print(f"\n💾 Creando backup: {BACKUP_SVG}")
        shutil.copy(OUTPUT_SVG, BACKUP_SVG)

    print("\n🎨 Generando SVG...")
    generate_svg(layers, OUTPUT_SVG)

    # Exportar a PNG automáticamente
    print("\n🖼️  Exportando a PNG...")
    try:
        subprocess.run(
            ["rsvg-convert", "-w", "2000", str(OUTPUT_SVG), "-o", str(OUTPUT_PNG)],
            check=True,
            capture_output=True
        )
        print(f"   ✅ PNG generado: {OUTPUT_PNG}")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Error al generar PNG: {e}")
        print(f"   💡 Instala librsvg: brew install librsvg")
    except FileNotFoundError:
        print(f"   ⚠️  rsvg-convert no encontrado")
        print(f"   💡 Instala librsvg: brew install librsvg")

    print(f"\n✨ Proceso completado!")
    print(f"   📄 SVG: {OUTPUT_SVG}")
    print(f"   🖼️  PNG: {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
