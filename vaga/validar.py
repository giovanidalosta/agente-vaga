"""CLI: python -m vaga.validar <descricao.md> --modelo <modelo-vaga.md> [--exigir TERMO ...]

Saída: 0 = válido (imprime OK), 1 = inválido (um erro por linha), 2 = erro de uso/arquivo.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vaga.modelo import secoes_do_modelo
from vaga.validador import validar_descricao


def _utf8(stream) -> None:
    # No Windows o console pode não ser UTF-8; evita UnicodeEncodeError com acentos.
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def _ler(caminho: str) -> str:
    try:
        return Path(caminho).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"arquivo não encontrado: {caminho}") from None


def main(argv: list[str] | None = None) -> int:
    _utf8(sys.stdout)
    _utf8(sys.stderr)
    parser = argparse.ArgumentParser(prog="python -m vaga.validar",
                                     description="Valida uma descrição de vaga contra o modelo da empresa.")
    parser.add_argument("descricao", help="arquivo Markdown da descrição gerada")
    parser.add_argument("--modelo", required=True, help="arquivo Markdown do modelo de vaga")
    parser.add_argument("--exigir", action="append", default=[], metavar="TERMO",
                        help="termo que precisa aparecer no texto (pode repetir)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0

    try:
        modelo = _ler(args.modelo)
        descricao = _ler(args.descricao)
    except (FileNotFoundError, UnicodeDecodeError, OSError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2

    secoes = secoes_do_modelo(modelo)
    if not secoes:
        print(f"erro: modelo não possui seções '## ': {args.modelo}", file=sys.stderr)
        return 2

    erros = validar_descricao(descricao, secoes, args.exigir)
    if erros:
        print("\n".join(erros))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
