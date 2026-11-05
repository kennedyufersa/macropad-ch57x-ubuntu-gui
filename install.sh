#!/usr/bin/env bash

# Baixa o executável ch57x-keyboard-tool para esta pasta.
# (Este repositório não inclui executáveis de terceiros,
# portanto, é necessário executar este script pelo menos uma vez.)
#
# Se a versão da glibc do sistema for antiga (por exemplo, Ubuntu 22.04 = 2.35),
# as versões mais recentes podem exigir GLIBC_2.38 e não funcionar.
# Por isso, o script testa várias versões em sequência e seleciona
# a primeira que consegue executar corretamente.

set -e
cd "$(dirname "$0")"

REPO="kriomant/ch57x-keyboard-tool"

case "$(uname -m)" in
  x86_64)  ARCH="x86_64-unknown-linux-gnu" ;;
  aarch64) ARCH="aarch64-unknown-linux-gnu" ;;
  *) echo "Arquitetura não suportada: $(uname -m)"; exit 1 ;;
esac

# Testa as versões da mais recente para a mais antiga.
# Em sistemas com versões antigas da glibc, pode ser necessário
# utilizar a versão v1.5.0 como alternativa.
VERSIONS=("v1.7.0" "v1.6.2" "v1.5.4" "v1.5.0")

OUT="ch57x-keyboard-tool"

for v in "${VERSIONS[@]}"; do
  url="https://github.com/$REPO/releases/download/$v/ch57x-keyboard-tool-$ARCH.tar.gz"

  echo "==> Tentando instalar a versão: $v"

  if curl -fsSL --max-time 60 -o /tmp/ch57x.tgz "$url" 2>/dev/null; then

    tar xzf /tmp/ch57x.tgz -C /tmp ch57x-keyboard-tool 2>/dev/null || tar xzf /tmp/ch57x.tgz -C /tmp

    if /tmp/ch57x-keyboard-tool --help >/dev/null 2>&1; then

      cp /tmp/ch57x-keyboard-tool "./$OUT"
      chmod +x "./$OUT"

      echo "Instalação concluída: $(pwd)/$OUT (versão $v)"

      rm -f /tmp/ch57x.tgz /tmp/ch57x-keyboard-tool

      exit 0

    else
      echo "   A versão $v não é compatível com este sistema (glibc ou outras dependências)."
      echo "   Tentando a próxima versão..."
    fi
  fi
done

echo "Falha na instalação: nenhuma versão compatível foi encontrada."
echo "Pode ser necessário compilar o programa a partir do código-fonte."

exit 1