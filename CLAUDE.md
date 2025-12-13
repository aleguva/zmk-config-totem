# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Objetivo del Proyecto

Migración gradual al layout Miryoku siguiendo estos pasos:
1. Verificar funcionamiento Bluetooth
2. Verificar funcionamiento con dongle Prospector
3. Migración paso a paso a Miryoku

**Filosofía**: Cambios pequeños y commits regulares. NO hacer cambios grandes que puedan causar arrepentimientos.

## Build System

El firmware se construye automáticamente via GitHub Actions al hacer push. Los archivos .uf2 se descargan de los artifacts del workflow.

```bash
git add .
git commit -m "Mensaje descriptivo"
git push
```

Build targets en `build.yaml`: `totem_left`, `totem_right`, `totem_dongle prospector_adapter`, `settings_reset`.

## Estructura

- `config/totem.keymap` - Keymap principal (6 capas: BASE, NAV, SYM, ADJ, TVP1, TVP2)
- `config/totem.conf` - Configuración del teclado
- `config/west.yml` - Dependencias (ZMK + prospector-zmk-module en branch core/zephyr-4-1)
- `config/boards/shields/totem/*.overlay` - Definición hardware

## Keymap Actual

- BASE: Colemak-DH con home row mods (GACS en ARST)
- NAV: Layer-tap en TAB - flechas, numpad, brackets
- SYM: Layer-tap en ESC - símbolos, umlauts, media
- ADJ: Momentary desde NAV+SYM - BT, reset, F-keys
- TVP1/2: Capas para app específica, toggle con combo (pos 11+12+13)

## Flashing

1. Descargar firmware.zip de GitHub Actions
2. Doble click reset en el teclado
3. Arrastrar el archivo .uf2 correspondiente

## Modificaciones Comunes

Editar `config/totem.keymap` para cambiar bindings. Usar keycodes de https://zmk.dev/docs/codes/

Editar `config/totem.conf` para opciones de configuración ZMK.
