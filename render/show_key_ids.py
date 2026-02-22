#!/usr/bin/env python3
"""
Genera un SVG simple mostrando los IDs de cada tecla
"""

import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SVG_TEMPLATE = REPO_ROOT / "docs" / "images" / "TOTEM_layout_template.svg"
OUTPUT_SVG = REPO_ROOT / "docs" / "images" / "TOTEM_key_ids.svg"

# Leer template
tree = ET.parse(SVG_TEMPLATE)
root = tree.getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}

# Inicio del SVG
svg_parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<svg xmlns="http://www.w3.org/2000/svg"',
    '     width="733.16" height="267.46"',
    '     viewBox="0 0 733.16 267.46">',
    '',
    '  <defs>',
    '    <style>',
    '      .cls-key {',
    '        fill: #1f2630;',
    '        stroke: #58a6ff;',
    '        stroke-width: 0.6px;',
    '      }',
    '      text {',
    '        font-family: monospace;',
    '        text-anchor: middle;',
    '        dominant-baseline: middle;',
    '        fill: #58a6ff;',
    '        font-size: 14px;',
    '        font-weight: bold;',
    '      }',
    '    </style>',
    '  </defs>',
    '',
    '  <rect width="733.16" height="267.46" fill="#0d1117"/>',
    '',
    '  <g id="keys">',
]

# Copiar rectángulos de teclas con IDs
for i in range(38):
    key_id = f"k{i:02d}"
    rect = root.find(f".//svg:rect[@id='{key_id}']", ns)

    if rect is not None:
        rect_attrs = rect.attrib.copy()
        rect_attrs['class'] = 'cls-key'
        attr_str = ' '.join(f'{k}="{v}"' for k, v in rect_attrs.items())
        svg_parts.append(f'    <rect {attr_str}/>')

        # Añadir texto con el ID
        x = float(rect_attrs.get('x', 0))
        y = float(rect_attrs.get('y', 0))
        width = float(rect_attrs.get('width', 49.61))
        height = float(rect_attrs.get('height', 46.77))

        cx = x + width / 2
        cy = y + height / 2

        # Extraer rotación si existe
        transform = rect_attrs.get('transform', '')
        if transform:
            svg_parts.append(f'    <text x="{cx}" y="{cy}" transform="{transform}">{key_id}</text>')
        else:
            svg_parts.append(f'    <text x="{cx}" y="{cy}">{key_id}</text>')

svg_parts.append('  </g>')
svg_parts.append('</svg>')

# Escribir archivo
OUTPUT_SVG.write_text('\n'.join(svg_parts), encoding='utf-8')
print(f"✅ SVG generado: {OUTPUT_SVG}")
