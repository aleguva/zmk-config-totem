import re
from pathlib import Path

KEYMAP_FILE = "totem.keymap"
TOTAL_KEYS = 38


def clean_token(token: str) -> str:
    """
    Convierte tokens ZMK a una etiqueta legible
    """
    token = token.strip()

    if token in ("&trans",):
        return ""

    # &kp Q, &kp COMMA, &kp FSLH...
    if token.startswith("&kp "):
        return token.replace("&kp ", "")

    # &mt LGUI A  → A
    if token.startswith("&mt "):
        return token.split()[-1]

    # &lt NAV TAB → TAB
    if token.startswith("&lt "):
        return token.split()[-1]

    # &mo BUTTON → BTN
    if token.startswith("&mo "):
        return "BTN"

    # Mouse buttons
    if token.startswith("&mkp "):
        return token.replace("&mkp ", "M")

    # Fallback (visible para depuración)
    return token.replace("&", "")


def parse_layers(text: str) -> dict:
    layers = {}

    # Encuentra bloques *_layer { ... bindings = < ... >; }
    pattern = re.compile(
        r'(\w+)_layer\s*{.*?bindings\s*=\s*<([^>]+)>;',
        re.S
    )

    for layer_name, bindings_block in pattern.findall(text):
        tokens = [
            t for t in bindings_block.replace("\n", " ").split()
            if not t.startswith("//")
        ]

        keys = []
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Detectar combinaciones (&mt, &lt necesitan 3 tokens)
            if token in ("&mt", "&lt"):
                combined = " ".join(tokens[i:i+3])
                keys.append(clean_token(combined))
                i += 3
            else:
                keys.append(clean_token(token))
                i += 1

        # Ajuste de seguridad
        if len(keys) != TOTAL_KEYS:
            raise ValueError(
                f"Capa {layer_name} tiene {len(keys)} teclas (esperadas {TOTAL_KEYS})"
            )

        layers[layer_name.upper()] = keys

    return layers


if __name__ == "__main__":
    text = Path(KEYMAP_FILE).read_text(encoding="utf-8")
    layers = parse_layers(text)

    for layer, keys in layers.items():
        print(f"\n[{layer}]")
        for i, k in enumerate(keys):
            print(f"k{i:02d}: {k}")
