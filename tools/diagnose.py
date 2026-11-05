#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnóstico de entradas brutas do MacroPad.

Mostra os eventos enviados por cada tecla e pelo botão giratório.
Uso: feche primeiro a interface do MacroPad e execute:
       python3 tools/diagnose.py
Depois, pressione lentamente as teclas 1 a 6 e gire/pressione o knob.
Copie toda a saída se precisar analisá-la. Use Ctrl+C para encerrar.
"""
import sys, time
import evdev
from evdev import ecodes

VENDOR, PRODUCT = 0x1189, 0x8890

devs = []
for path in evdev.list_devices():
    try:
        d = evdev.InputDevice(path)
    except Exception:
        continue
    if d.info.vendor == VENDOR and d.info.product == PRODUCT:
        devs.append(d)

if not devs:
    print("MacroPad (1189:8890) não encontrado. Verifique a conexão e as permissões.")
    sys.exit(1)

print("=== Interfaces encontradas ===")
for d in devs:
    print(f"  {d.path}  '{d.name}'  caps:", end=" ")
    caps = d.capabilities(verbose=False)
    print("EV_KEY" if ecodes.EV_KEY in caps else "",
          "EV_REL" if ecodes.EV_REL in caps else "")
print("\n=== Pressione cada tecla e use o knob, um por vez (Ctrl+C para encerrar) ===\n")

import select
fdmap = {d.fd: d for d in devs}
try:
    while True:
        r, _, _ = select.select(fdmap.keys(), [], [], 1.0)
        for fd in r:
            dev = fdmap[fd]
            for ev in dev.read():
                if ev.type == ecodes.EV_KEY:
                    name = ecodes.KEY.get(ev.code, f"code{ev.code}")
                    val = {0: "solta", 1: "PRESSIONADA", 2: "repetição"}.get(ev.value, ev.value)
                    tag = dev.path.rsplit("/", 1)[-1]
                    print(f"[{tag}] KEY  {name} (code={ev.code})  {val}")
                elif ev.type == ecodes.EV_REL:
                    name = ecodes.REL.get(ev.code, f"rel{ev.code}")
                    tag = dev.path.rsplit("/", 1)[-1]
                    print(f"[{tag}] REL  {name}  value={ev.value}")
except KeyboardInterrupt:
    print("\nEncerrado.")
