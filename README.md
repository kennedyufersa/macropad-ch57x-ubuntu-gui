# MacroPad CH57x no Ubuntu — instalação e interface em português

Guia para instalar e configurar um **macro keypad TISHRIC de 6 teclas e 1 knob** no Ubuntu usando o projeto [macropad-ch57x-ubuntu-gui](https://github.com/iam-raccoon/macropad-ch57x-ubuntu-gui).

> **Pré-requisito:** o arquivo `padconf_pt_BR.py` já deve estar dentro da pasta `macropad-ch57x-ubuntu-gui`. Ele é uma versão traduzida da interface original.

## 1. Instalar dependências

Abra um terminal e execute:

```bash
sudo apt update
sudo apt install -y git python3 python3-pyqt5 curl x11-xserver-utils
```

## 2. Clonar o projeto

Se ainda não clonou o repositório:

```bash
cd ~
git clone https://github.com/kennedyufersa/macropad-ch57x-ubuntu-gui.git
```

Entre na pasta:

```bash
cd ~/macropad-ch57x-ubuntu-gui
```

**Se já clonou o projeto, não execute `git clone` novamente:** apenas entre na pasta existente.

Confira os arquivos:

```bash
ls -la
```

Confirme que `padconf_pt_BR.py` está nessa pasta antes de seguir para a etapa 5.

## 3. Instalar a ferramenta de gravação

Dentro da pasta do projeto, execute:

```bash
./install.sh
```

Esse script instala o `ch57x-keyboard-tool`, responsável por gravar a configuração no keypad.

Confira se o executável foi instalado:

```bash
ls -l ch57x-keyboard-tool
```

## 4. Configurar permissões USB

```bash
sudo ./setup-udev.sh
```

Depois:

1. Desconecte o keypad da porta USB.
2. Conecte-o novamente.
3. Se for solicitado atualizar sua associação ao grupo `plugdev`, encerre a sessão do Ubuntu e entre novamente.

## 5. Ativar a interface em português brasileiro

Como `padconf_pt_BR.py` **já está na pasta do projeto**, não é necessário copiá-lo de `Downloads`.

Faça um backup do arquivo original e instale a tradução:

```bash
cp padconf.py padconf.py.bak
cp padconf_pt_BR.py padconf.py
```

Verifique a sintaxe Python:

```bash
python3 -m py_compile padconf.py
```

Se o comando não apresentar mensagens, não foram detectados erros de sintaxe.

Para restaurar a versão original posteriormente:

```bash
cp padconf.py.bak padconf.py
```

## 6. Verificar se o keypad é compatível

```bash
lsusb | grep 1189
```

O projeto declara suporte aos seguintes IDs USB:

- `1189:8890`
- `1189:8840`
- `1189:8842`

Se nenhum desses aparecer, **não tente gravar ainda**: identifique primeiro o dispositivo com `lsusb`.

## 7. Abrir a interface gráfica

```bash
python3 padconf.py
```

A janela deverá mostrar as seis teclas e as três ações do knob: rotação anti-horária, pressionamento e rotação horária.

### Verificar a sessão gráfica

```bash
echo "$XDG_SESSION_TYPE"
```

O projeto foi desenvolvido para **GNOME com X11**. No Wayland, a interface pode abrir, mas a integração com atalhos para iniciar aplicativos pode não funcionar como esperado.

## 8. Configurar teclas e knob

1. Clique na tecla ou na ação do knob que deseja configurar.
2. Escolha o tipo de ação: **Tecla / Atalho**, **Mídia / Volume** ou **Abrir aplicativo**.
3. Escolha ou digite o valor.
4. Clique em **Salvar configuração da tecla**.
5. Repita para os demais controles.

Exemplos de atalhos:

| Ação | Valor |
| --- | --- |
| Copiar | `ctrl-c` |
| Colar | `ctrl-v` |
| Recortar | `ctrl-x` |
| Desfazer | `ctrl-z` |
| Salvar | `ctrl-s` |
| Alternar janelas | `alt-tab` |
| Atualizar | `f5` |

Exemplo para o knob:

| Movimento | Valor |
| --- | --- |
| Anti-horário | `volumedown` |
| Pressionar | `mute` |
| Horário | `volumeup` |

## 9. Gravar as configurações no dispositivo

Depois de configurar todos os controles:

1. Clique em **Salvar e gravar no dispositivo**.
2. Aguarde a mensagem de confirmação.
3. Teste as teclas e o knob.

> **Atenção:** salvar a configuração de uma tecla apenas atualiza o estado local. Para gravar no keypad, use **Salvar e gravar no dispositivo**.

As funções de teclado e mídia ficam armazenadas no dispositivo compatível. A opção **Abrir aplicativo** depende também de atalhos registrados no GNOME do computador.

## 10. Abrir o programa nas próximas vezes

```bash
cd ~/macropad-ch57x-ubuntu-gui
python3 padconf.py
```

Não é necessário repetir a instalação.

## Resumo dos comandos

> Use este bloco em uma **instalação nova**, após colocar `padconf_pt_BR.py` na pasta clonada. Se o projeto já estiver clonado, pule o `git clone`.

```bash
# Dependências
sudo apt update
sudo apt install -y git python3 python3-pyqt5 curl x11-xserver-utils

# Clone (somente se ainda não existir)
cd ~
git clone https://github.com/iam-raccoon/macropad-ch57x-ubuntu-gui.git
cd ~/macropad-ch57x-ubuntu-gui

# Instalação e permissões
./install.sh
sudo ./setup-udev.sh

# Desconecte e reconecte o keypad antes de continuar.

# Backup e tradução (padconf_pt_BR.py já presente nesta pasta)
cp padconf.py padconf.py.bak
cp padconf_pt_BR.py padconf.py
python3 -m py_compile padconf.py

# Verificação do dispositivo
lsusb | grep 1189

# Iniciar
python3 padconf.py
```

## Solução de problemas

**`cd: ... No such file or directory`**: localize a pasta clonada com:

```bash
find ~ -type d -name 'macropad-ch57x-ubuntu-gui' 2>/dev/null
```

**`cp: cannot stat 'padconf_pt_BR.py'`**: o arquivo traduzido não está na pasta atual. Confira com `pwd` e `ls -la`.

**`Access denied` ao gravar**: execute `sudo ./setup-udev.sh`, reconecte o dispositivo e confira se a sessão do usuário precisa ser reiniciada.

**Interface abre, mas atalhos para aplicativos falham**: confira `echo "$XDG_SESSION_TYPE"`; o projeto utiliza recursos do GNOME/X11.

**Todas as teclas enviam o mesmo código antes da programação**: esse comportamento é relatado pelo projeto para dispositivos ainda não configurados.

## Referências

- [Interface gráfica macropad-ch57x-ubuntu-gui](https://github.com/iam-raccoon/macropad-ch57x-ubuntu-gui)
- [Ferramenta de gravação ch57x-keyboard-tool](https://github.com/kriomant/ch57x-keyboard-tool)
