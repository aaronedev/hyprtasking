#!/usr/bin/env python3
"""Check handler-test launcher arguments and missing XKB diagnostics.

Run: python3 tests/portability.py
Requires Meson, Ninja, a C++23 compiler, pkg-config and plugin build dependencies.
The compiler wrapper simulates the c++2b fallback; it is not an older compiler.
No plugin is loaded and no cross-architecture binary is built.
"""

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)

with tempfile.TemporaryDirectory(prefix="portability-", dir=BUILD) as directory:
    root = Path(directory)
    wrapper = root / "compiler with spaces"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "if sys.argv[1] != 'wrapper argument with spaces':\n"
        "    raise SystemExit('wrapper argument was split')\n"
        "args = sys.argv[2:]\n"
        "if '-std=c++23' in args:\n"
        "    raise SystemExit(91)\n"
        "os.execvp('c++', ['c++', *args])\n"
    )
    wrapper.chmod(0o755)
    native = root / "native.ini"
    native.write_text(
        "[binaries]\ncpp = ['" + str(wrapper)
        + "', 'wrapper argument with spaces']\n"
    )
    subprocess.run(
        ["meson", "setup", str(root / "build"), str(ROOT), "--native-file", str(native)],
        check=True,
    )
    subprocess.run(
        ["meson", "test", "-C", str(root / "build"), "--print-errorlogs"], check=True
    )
    empty = root / "empty-xkb"
    empty.mkdir()
    env = os.environ.copy()
    env["XKB_CONFIG_ROOT"] = str(empty)
    env["XKB_CONFIG_EXTRA_PATH"] = str(empty)
    result = subprocess.run(
        ["python3", str(ROOT / "tests/handlers.py")],
        env=env, capture_output=True, text=True,
    )
    if (result.returncode == 0
        or "German XKB keymap must initialize" not in result.stderr
        or "SIGSEGV" in result.stderr):
        raise RuntimeError("missing XKB data did not report a controlled initialization error")
    print("compiler argument round-trip, c++2b fallback and missing XKB data: passed")
