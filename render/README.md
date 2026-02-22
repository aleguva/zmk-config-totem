# Layout Renderer

Scripts para generar automáticamente visualizaciones del layout del teclado desde `config/totem.keymap`.

## Archivos

- **parse_totem_keymap.py** - Parser que extrae las capas del keymap de ZMK
- **render_unified.py** ⭐ - Genera layout unificado con todas las capas visibles en una sola imagen
- **render_svg.py** - Genera SVG con capas separadas verticalmente (legacy)

## Uso

### Layout Unificado (Recomendado)

```bash
cd render
python3 render_unified.py
```

Esto automáticamente:
1. Lee `config/totem.keymap`
2. Parsea las 5 capas principales (BASE, NAV, SYM, NUM, FUN)
3. Genera `docs/images/TOTEM_layout.svg` con **todas las capas superpuestas en una sola imagen**
4. Exporta automáticamente a `docs/images/TOTEM_layout.png`
5. Guarda backup del SVG anterior en `docs/images/TOTEM_layout_backup.svg`

**Características del layout unificado:**

**Distribución asimétrica (izquierda vs derecha del teclado):**

Mitad izquierda:
```
BASE (↖)    SYM (↗)
NAV (↙)     NUM (↘)
```

Mitad derecha:
```
BASE (↖)    MOUSE (↗)
MEDIA (↙)   NAV (↘)
```

- ✨ **BASE siempre en esquina superior izquierda** (fuente 12px, azul #58a6ff)
- 🔄 **Todos los textos mantienen la rotación de su tecla**
- 🎨 **Colores distintivos por capa**
- 🚫 **No muestra teclas transparentes** (&trans)
- 📦 **Efecto 3D**: Rectángulo de profundidad simulando altura de tecla
- 🖼️ **Reborde**: Padding de 20px alrededor del layout

### Layout Separado (Legacy)

Para generar capas separadas verticalmente:

```bash
cd render
python3 render_svg.py
```

## Características

### Colores por capa (Layout Unificado)
- **BASE**: Azul claro (#58a6ff) - fuente 12px
- **NAV**: Azul cielo (#79c0ff) - fuente 8px
- **SYM**: Naranja (#ffa657) - fuente 8px
- **NUM**: Naranja oscuro (#f0883e) - fuente 8px
- **MOUSE**: Azul pastel (#a5d6ff) - fuente 8px
- **MEDIA**: Rosa (#f778ba) - fuente 8px

### Símbolos especiales
El parser convierte códigos ZMK a símbolos legibles:
- **Teclas especiales**: ⌫ (Backspace), ↵ (Enter), ⎋ (Escape), ⇥ (Tab), etc.
- **Modificadores**: ⌘ (Command), ⌃ (Control), ⌥ (Option), ⇧ (Shift)
- **Combinaciones**: ⌘C (Copy), ⌘V (Paste), ⌘⇧Z (Redo), etc.
- **Navegación**: ← ↓ ↑ → (Flechas)
- **Media**: ⏮ ⏭ ⏯ ⏹ 🔉 🔊 🔇 🔅 🔆
- **Layer taps**: `ESC↓MED` indica Escape que al mantener activa MEDIA layer
- **Home row mods**: Muestra la letra principal y el modificador en dos líneas

## Requisitos

```bash
# Para exportar a PNG (ya instalado)
brew install librsvg
```

## Automatización

Puedes agregar esto a un hook de pre-commit para regenerar automáticamente la imagen cada vez que cambies el keymap:

```bash
#!/bin/bash
# .git/hooks/pre-commit
cd render && python3 render_svg.py
git add docs/images/TOTEM_layout.svg docs/images/TOTEM_layout.png
```
