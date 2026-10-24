from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

START = "# >>> mirror >>>"
END = "# <<< mirror <<<"


def main() -> int:
    if sys.version_info < (3, 11):
        raise SystemExit("Mirror requires Python 3.11 or newer.")
    root = Path(__file__).resolve().parent
    environment = root / ".venv"
    executable = environment / "bin" / "mirror"
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    subprocess.run(
        [str(environment / "bin" / "python"), "-m", "pip", "install", "--no-deps", str(root)],
        check=True,
    )
    subprocess.run([str(executable), "init"], check=True)

    zshrc = Path.home() / ".zshrc"
    existing = zshrc.read_text(encoding="utf-8") if zshrc.exists() else ""
    block = (
        f"{START}\n"
        f"export MIRROR_BIN={shlex.quote(str(executable))}\n"
        f"export PATH={shlex.quote(str(environment / 'bin'))}:\"$PATH\"\n"
        f"source {shlex.quote(str(root / 'shell' / 'mirror.zsh'))}\n"
        f"{END}\n"
    )
    has_start = START in existing
    has_end = END in existing
    if has_start != has_end:
        raise SystemExit("Mirror's .zshrc block is incomplete; no changes were made.")
    if has_start:
        before, remainder = existing.split(START, 1)
        _, after = remainder.split(END, 1)
        updated = before + block + after.removeprefix("\n")
    else:
        separator = "" if not existing or existing.endswith("\n") else "\n"
        updated = existing + separator + ("\n" if existing else "") + block
    mode = stat.S_IMODE(zshrc.stat().st_mode) if zshrc.exists() else 0o600
    zshrc.write_text(updated, encoding="utf-8")
    os.chmod(zshrc, mode)
    print("installed. open a new terminal; mirror starts with zsh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
