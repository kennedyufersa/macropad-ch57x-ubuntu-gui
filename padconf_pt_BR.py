#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface de configuração do MacroPad (ch57x / 1189:8890, 6 teclas e botão giratório).

- Configure cada tecla e o botão giratório com atalhos, controles de mídia ou abertura de aplicativos.
- Ao salvar, gera um YAML para o ch57x-keyboard-tool e o grava no dispositivo.
- Para abrir aplicativos, associa automaticamente F14 a F18 (keysyms XF86Launch5 a 9)
  e gerencia atalhos personalizados do GNOME (keysym para comando).
- Configuração principal: ~/.config/macropad/padconf.json (origem do YAML e dos atalhos).

Permissões: acesso USB via regra udev 50-ch57x (sem sudo); execução em sessão GNOME (gsettings).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "ch57x-keyboard-tool")
YAML_PATH = os.path.join(HERE, "config.yaml")
STATE_DIR = os.path.expanduser("~/.config/macropad")
STATE_PATH = os.path.join(STATE_DIR, "padconf.json")

VENDOR_ID = "4489"      # 0x1189
PRODUCT_ID = "34960"    # 0x8890

# Teclas de função reservadas para abrir aplicativos (F13 excluída por conflito com Configurações).
# Código evdev = código X11 - 8. F14 corresponde ao código X11 192; F18, ao 196.
LAUNCH_FKEYS = [
    ("f14", 192), ("f15", 193), ("f16", 194), ("f17", 195), ("f18", 196),
]

MEDIA_OPTIONS = [
    ("volumeup", "Volume ▲"), ("volumedown", "Volume ▼"), ("mute", "Silenciar"),
    ("play", "Reproduzir/Pausar"), ("next", "Próxima faixa"), ("previous", "Faixa anterior"),
    ("wheelup", "Rolagem ▲"), ("wheeldown", "Rolagem ▼"), ("click", "Clique do mouse"),
]
KEY_PRESETS = [
    "1", "2", "3", "escape", "enter", "tab", "space", "backspace", "delete",
    "f5", "left", "right", "up", "down", "home", "end",
    "ctrl-c", "ctrl-v", "ctrl-x", "ctrl-z", "ctrl-a", "ctrl-s",
    "ctrl-shift-t", "alt-tab", "shift-tab",
]
APP_PRESETS = [
    ("code", "VS Code"), ("terminator", "Terminator"),
    ("gnome-terminal", "Terminal GNOME"), ("firefox", "Firefox"),
    ("nautilus", "Gerenciador de arquivos"), ("gnome-control-center", "Configurações"),
]

BUTTON_LABELS = ["Superior esquerda", "Superior central", "Superior direita",
                 "Inferior esquerda", "Inferior central", "Inferior direita"]
KNOB_LABELS = {"ccw": "Knob ◀ Anti-horário", "press": "Knob ● Pressionar", "cw": "Knob ▶ Horário"}

DEFAULT_STATE = {
    "buttons": [
        {"type": "key", "value": "1"},
        {"type": "key", "value": "2"},
        {"type": "key", "value": "escape"},
        {"type": "launch", "value": "code"},
        {"type": "launch", "value": "terminator"},
        {"type": "key", "value": "f5"},
    ],
    "knob": {
        "ccw": {"type": "media", "value": "volumedown"},
        "press": {"type": "media", "value": "mute"},
        "cw": {"type": "media", "value": "volumeup"},
    },
}


# ---------------- Carregamento e salvamento do estado ----------------
def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                st = json.load(f)
            st.setdefault("buttons", DEFAULT_STATE["buttons"])
            st.setdefault("knob", DEFAULT_STATE["knob"])
            return st
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_STATE))


def save_state(st):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


# ---------------- Identificação de keysyms (abertura de aplicativos) ----------------
def detect_launch_keysyms():
    """Consulta os keysyms reais de F14 a F18 no X11 via xmodmap."""
    result = {}
    try:
        out = subprocess.check_output(["xmodmap", "-pke"], text=True,
                                      stderr=subprocess.DEVNULL)
    except Exception:
        return result
    kc_sym = {}
    for line in out.splitlines():
        m = re.match(r"keycode\s+(\d+)\s*=\s*(\S+)?", line)
        if m and m.group(2):
            kc_sym[int(m.group(1))] = m.group(2)
    for fkey, kc in LAUNCH_FKEYS:
        sym = kc_sym.get(kc)
        if sym and sym != "NoSymbol":
            result[fkey] = sym
    return result


# ---------------- Geração do YAML ----------------
def action_to_chord(action, launch_alloc):
    """Converte uma ação na combinação de teclas usada pelo YAML do ch57x."""
    t = action.get("type")
    v = action.get("value", "")
    if t == "launch":
        # Tecla de função atribuída à ação de abertura de aplicativo.
        return launch_alloc.get(id(action), "escape")
    return v or "escape"


def build_yaml_and_launches(state):
    """Retorna o YAML e os atalhos de aplicativos a registrar (keysym, comando)."""
    keysyms = detect_launch_keysyms()          # {fkey: keysym}
    pool = [fk for fk, _ in LAUNCH_FKEYS if fk in keysyms]
    launch_alloc = {}                          # id(action) -> fkey
    launches = []                              # (keysym, command)
    warnings = []

    # Percorre as teclas e atribui uma tecla de função a cada abertura de aplicativo.
    for i, action in enumerate(state["buttons"]):
        if action.get("type") == "launch":
            if pool:
                fk = pool.pop(0)
                launch_alloc[id(action)] = fk
                launches.append((keysyms[fk], action.get("value", "").strip()))
            else:
                warnings.append("Limite de aplicativos excedido (F14 a F18 esgotadas). Ignorando '%s'."
                                % action.get("value"))
                launch_alloc[id(action)] = "escape"
    # O botão giratório também pode abrir aplicativos.
    for k in ("ccw", "press", "cw"):
        action = state["knob"][k]
        if action.get("type") == "launch":
            if pool:
                fk = pool.pop(0)
                launch_alloc[id(action)] = fk
                launches.append((keysyms[fk], action.get("value", "").strip()))
            else:
                warnings.append("Limite de aplicativos excedido: ignorando ação do botão giratório '%s'." % k)
                launch_alloc[id(action)] = "escape"

    b = [action_to_chord(a, launch_alloc) for a in state["buttons"]]
    kn = {k: action_to_chord(state["knob"][k], launch_alloc)
          for k in ("ccw", "press", "cw")}

    yaml = (
        "orientation: normal\n"
        "rows: 2\n"
        "columns: 3\n"
        "knobs: 1\n"
        "layers:\n"
        "  - buttons:\n"
        '      - ["%s", "%s", "%s"]\n'
        '      - ["%s", "%s", "%s"]\n'
        "    knobs:\n"
        '      - ccw: "%s"\n'
        '        press: "%s"\n'
        '        cw: "%s"\n'
    ) % (b[0], b[1], b[2], b[3], b[4], b[5], kn["ccw"], kn["press"], kn["cw"])
    return yaml, launches, warnings


# ---------------- Aplicação: gravação USB e atalhos ----------------
def run_tool(args, stdin=None):
    return subprocess.run([TOOL] + args, input=stdin, capture_output=True, text=True)


def sync_gnome_shortcuts(launches):
    """Recria os atalhos personalizados macropad-* com base em launches."""
    schema = "org.gnome.settings-daemon.plugins.media-keys"
    base = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"

    def gset(*a):
        subprocess.run(["gsettings"] + list(a), capture_output=True, text=True)

    def gget(*a):
        return subprocess.run(["gsettings", "get"] + list(a),
                              capture_output=True, text=True).stdout.strip()

    # Remove os atalhos macropad-* da lista atual.
    cur = gget(schema, "custom-keybindings")
    paths = re.findall(r"'([^']+)'", cur)
    paths = [p for p in paths if "/macropad-" not in p]

    # Registra novos atalhos para abrir aplicativos.
    for idx, (keysym, command) in enumerate(launches):
        slot = "macropad-app%d" % idx
        path = "%s/%s/" % (base, slot)
        kb = "%s.custom-keybinding:%s" % (schema, path)
        gset("set", kb, "name", "MacroPad %s" % command)
        gset("set", kb, "command", command)
        gset("set", kb, "binding", keysym)
        paths.append(path)

    newlist = "[%s]" % ", ".join("'%s'" % p for p in paths) if paths else "@as []"
    gset("set", schema, "custom-keybindings", newlist)


def apply_state(state):
    """Gera e valida YAML, grava no dispositivo e sincroniza atalhos; retorna sucesso e mensagem."""
    yaml, launches, warnings = build_yaml_and_launches(state)
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        f.write(yaml)

    v = run_tool(["validate"], stdin=yaml)
    if v.returncode != 0:
        return False, "Falha na validação do YAML:\n" + (v.stderr or v.stdout)

    up = run_tool(["--product-id", PRODUCT_ID, "upload"], stdin=yaml)
    if up.returncode != 0:
        return False, "Falha ao gravar no dispositivo:\n" + (up.stderr or up.stdout)

    try:
        sync_gnome_shortcuts(launches)
        sc_msg = "%d atalho(s) registrado(s)" % len(launches)
    except Exception as e:
        sc_msg = "Aviso ao registrar atalhos: %s" % e

    msg = "Configuração gravada no dispositivo. " + sc_msg
    if warnings:
        msg += "\nAtenção:\n- " + "\n- ".join(warnings)
    return True, msg


# ======================= GUI =======================
def make_gui(run=True):
    from PyQt5 import QtWidgets, QtCore

    class Main(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Configuração do MacroPad (ch57x 1189:8890)")
            self.state = load_state()
            self.sel = ("button", 0)
            self._build()
            self._refresh_cells()
            self._load_editor()

        def _build(self):
            central = QtWidgets.QWidget()
            self.setCentralWidget(central)
            root = QtWidgets.QHBoxLayout(central)

            left = QtWidgets.QVBoxLayout()
            left.addWidget(QtWidgets.QLabel("<b>Teclas (3 x 2)</b>"))
            grid = QtWidgets.QGridLayout()
            self.cell_btns = []
            for i in range(6):
                b = QtWidgets.QPushButton()
                b.setMinimumSize(140, 66)
                b.clicked.connect(lambda _, idx=i: self._select(("button", idx)))
                grid.addWidget(b, i // 3, i % 3)
                self.cell_btns.append(b)
            left.addLayout(grid)
            left.addWidget(QtWidgets.QLabel("<b>Botão giratório</b>"))
            knob = QtWidgets.QHBoxLayout()
            self.knob_btns = {}
            for k in ("ccw", "press", "cw"):
                b = QtWidgets.QPushButton()
                b.setMinimumSize(140, 52)
                b.clicked.connect(lambda _, kk=k: self._select(("knob", kk)))
                knob.addWidget(b)
                self.knob_btns[k] = b
            left.addLayout(knob)
            left.addStretch(1)
            root.addLayout(left)

            right = QtWidgets.QVBoxLayout()
            self.sel_label = QtWidgets.QLabel()
            right.addWidget(self.sel_label)
            right.addWidget(QtWidgets.QLabel("Tipo de ação"))
            self.type_combo = QtWidgets.QComboBox()
            self.type_combo.addItem("Tecla / Atalho", "key")
            self.type_combo.addItem("Mídia / Volume", "media")
            self.type_combo.addItem("Abrir aplicativo", "launch")
            self.type_combo.currentIndexChanged.connect(self._type_changed)
            right.addWidget(self.type_combo)

            right.addWidget(QtWidgets.QLabel("Valor"))
            self.key_combo = QtWidgets.QComboBox()
            self.key_combo.setEditable(True)
            self.key_combo.addItems(KEY_PRESETS)
            right.addWidget(self.key_combo)

            self.media_combo = QtWidgets.QComboBox()
            for mid, ml in MEDIA_OPTIONS:
                self.media_combo.addItem(ml, mid)
            right.addWidget(self.media_combo)

            self.app_combo = QtWidgets.QComboBox()
            self.app_combo.setEditable(True)
            for cmd, name in APP_PRESETS:
                self.app_combo.addItem("%s (%s)" % (name, cmd), cmd)
            right.addWidget(self.app_combo)

            self.hint = QtWidgets.QLabel()
            self.hint.setStyleSheet("color:#777;font-size:11px;")
            self.hint.setWordWrap(True)
            right.addWidget(self.hint)

            self.apply_slot_btn = QtWidgets.QPushButton("Salvar configuração da tecla")
            self.apply_slot_btn.clicked.connect(self._save_slot)
            right.addWidget(self.apply_slot_btn)

            right.addStretch(1)
            self.upload_btn = QtWidgets.QPushButton("💾 Salvar e gravar no dispositivo")
            self.upload_btn.setStyleSheet("font-weight:bold;padding:8px;")
            self.upload_btn.clicked.connect(self._apply_all)
            right.addWidget(self.upload_btn)
            self.status = QtWidgets.QLabel("Pronto")
            self.status.setWordWrap(True)
            right.addWidget(self.status)
            root.addLayout(right)

        def _cur_action(self):
            kind, key = self.sel
            if kind == "button":
                return self.state["buttons"][key]
            return self.state["knob"][key]

        def _select(self, sel):
            self.sel = sel
            self._refresh_cells()
            self._load_editor()

        def _load_editor(self):
            kind, key = self.sel
            name = BUTTON_LABELS[key] if kind == "button" else KNOB_LABELS[key]
            self.sel_label.setText("<b>Selecionado: %s</b>" % name)
            a = self._cur_action()
            idx = {"key": 0, "media": 1, "launch": 2}.get(a.get("type"), 0)
            self.type_combo.setCurrentIndex(idx)
            self._type_changed()
            t, v = a.get("type"), a.get("value", "")
            if t == "media":
                mi = self.media_combo.findData(v)
                if mi >= 0:
                    self.media_combo.setCurrentIndex(mi)
            elif t == "launch":
                ai = self.app_combo.findData(v)
                if ai >= 0:
                    self.app_combo.setCurrentIndex(ai)
                else:
                    self.app_combo.setEditText(v)
            else:
                self.key_combo.setEditText(v)

        def _type_changed(self):
            t = self.type_combo.currentData()
            self.key_combo.setVisible(t == "key")
            self.media_combo.setVisible(t == "media")
            self.app_combo.setVisible(t == "launch")
            hints = {
                "key": "Nome da tecla ou combinação. Ex.: 1 · escape · f5 · ctrl-c · alt-tab · left",
                "media": "Associe aumentar/diminuir volume à rotação para usar como controle de volume.",
                "launch": "Informe um comando (ex.: code, firefox). Atribui F14 a F18 e registra atalho no GNOME.",
            }
            self.hint.setText(hints.get(t, ""))

        def _save_slot(self):
            t = self.type_combo.currentData()
            if t == "media":
                v = self.media_combo.currentData()
            elif t == "launch":
                idx = self.app_combo.currentIndex()
                typed = self.app_combo.currentText().strip()
                if (idx >= 0 and self.app_combo.itemText(idx) == typed
                        and self.app_combo.itemData(idx)):
                    v = self.app_combo.itemData(idx)   # Opção predefinida selecionada.
                else:
                    v = typed                          # Comando digitado manualmente.
            else:
                v = self.key_combo.currentText().strip()
            a = self._cur_action()
            a["type"] = t
            a["value"] = v
            save_state(self.state)
            self._refresh_cells()
            self.status.setText("Ação salva localmente. Para gravar no dispositivo, clique em 'Salvar e gravar no dispositivo'.")

        def _summary(self, a):
            t, v = a.get("type"), a.get("value", "")
            if t == "media":
                return "Mídia: %s" % dict(MEDIA_OPTIONS).get(v, v)
            if t == "launch":
                return "Executar: %s" % v
            return "Tecla: %s" % v

        def _refresh_cells(self):
            for i, b in enumerate(self.cell_btns):
                a = self.state["buttons"][i]
                b.setText("%s\n%s" % (BUTTON_LABELS[i], self._summary(a)))
                b.setStyleSheet("border:2px solid #2d7;font-weight:bold;"
                                if self.sel == ("button", i) else "")
            for k, b in self.knob_btns.items():
                a = self.state["knob"][k]
                b.setText("%s\n%s" % (KNOB_LABELS[k], self._summary(a)))
                b.setStyleSheet("border:2px solid #2d7;font-weight:bold;"
                                if self.sel == ("knob", k) else "")

        def _apply_all(self):
            self._save_slot()
            self.status.setText("Gravando configuração...")
            QtWidgets.QApplication.processEvents()
            ok, msg = apply_state(self.state)
            self.status.setText(("✅ " if ok else "❌ ") + msg)

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = Main()
    w.resize(760, 460)
    if not run:
        return app, w
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        ok, msg = apply_state(load_state())
        print(msg)
        sys.exit(0 if ok else 1)
    make_gui()
