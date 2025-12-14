# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Objetivo del Proyecto

Migración gradual al layout Miryoku siguiendo estos pasos:
1. ✅ Verificar funcionamiento Bluetooth - FUNCIONA
2. ✅ Verificar funcionamiento con dongle Prospector - FUNCIONA
3. ✅ Migración completa a Miryoku - IMPLEMENTADO
4. ⏳ Testing y ajustes incrementales para adaptación al trabajo

**Filosofía**: Cambios pequeños y commits regulares. NO hacer cambios grandes que puedan causar arrepentimientos.

## Estado Actual

- Bluetooth directo: ✅ Funcional
- Dongle Prospector: ✅ Funcional
- Miryoku 8 capas: ✅ Implementado, pendiente testing
- Problema conocido: Right muestra 0% batería en dongle (pendiente verificar tras carga)

## Build System

El firmware se construye automáticamente via GitHub Actions al hacer push. Los archivos .uf2 se descargan de los artifacts del workflow.

```bash
git add .
git commit -m "Mensaje descriptivo"
git push
```

Build targets en `build.yaml`: `totem_left`, `totem_right`, `totem_dongle prospector_adapter`, `settings_reset`.

## Estructura

- `config/totem.keymap` - Keymap principal (8 capas Miryoku)
- `config/totem.conf` - Configuración del teclado (pointing habilitado)
- `config/west.yml` - Dependencias (ZMK + prospector-zmk-module en branch core/zephyr-4-1)
- `config/boards/shields/totem/*.overlay` - Definición hardware

## Keymap Miryoku (8 capas)

- **BASE (0)**: Colemak-DH con home row mods (GUI/ALT/CTRL/SHIFT en ARST), US International layout
- **NAV (1)**: Navegación con flechas, clipboard ops (undo/cut/copy/paste/redo), page nav
- **MOUSE (2)**: Emulación de mouse (movimiento, scroll, botones) sin dispositivo apuntador físico
- **MEDIA (3)**: Controles multimedia (prev/next, vol+/-, play/stop/mute), brightness, BT profiles, output toggle
- **SYM (4)**: Símbolos para programación ({}&*()^%$#@!~|+:_)
- **NUM (5)**: Números y numpad ([7890]456123.-;=`\)
- **FUN (6)**: F-keys, system controls (BT, reset, bootloader)
- **BUTTON (7)**: Acceso simétrico a clipboard y mouse buttons (activado con outer pinkie keys)

## Flashing

1. Descargar firmware.zip de GitHub Actions
2. Doble click reset en el teclado
3. Arrastrar el archivo .uf2 correspondiente

## Modificaciones Comunes

Editar `config/totem.keymap` para cambiar bindings. Usar keycodes de https://zmk.dev/docs/codes/

Editar `config/totem.conf` para opciones de configuración ZMK.
