#!/usr/bin/env bash
# Instala a regra udev que concede ao grupo plugdev acesso de leitura e escrita ao MacroPad USB.
# Execute uma única vez com sudo; depois será possível gravar no pad sem sudo.
set -e
cd "$(dirname "$0")"
DEST=/etc/udev/rules.d/50-ch57x-macrokeyboard.rules
sudo cp udev/50-ch57x-macrokeyboard.rules "$DEST"
sudo udevadm control --reload-rules
sudo udevadm trigger --attr-match=idVendor=1189 --attr-match=idProduct=8890 || sudo udevadm trigger
echo "Concluído. Desconecte e reconecte o MacroPad USB para aplicar a regra."
echo "Para verificar se o usuário atual pertence ao grupo plugdev: id -nG | tr ' ' '\\n' | grep -x plugdev"
