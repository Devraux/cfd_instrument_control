[Download CFD Instrument Control](https://github.com/Devraux/cfd_instrument_control/releases/latest/download/cfd_instrument_control.exe)


BUILD SCRIPT

mkdir -p release/build_env

if [ ! -f release/build_env/.venv_build/Scripts/python.exe ]; then
    python -m venv release/build_env/.venv_build || exit 1
fi

PY="release/build_env/.venv_build/Scripts/python.exe"

"$PY" -m pip install --upgrade pip || exit 1
"$PY" -m pip install --upgrade pyinstaller numpy matplotlib pyserial pyvisa || exit 1

"$PY" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --hidden-import=serial \
  --name cfd_instrument_control \
  --distpath release/build_env/dist \
  --workpath release/build_env/build \
  --specpath release/build_env \
  main.py || exit 1

echo "release/build_env/dist/cfd_instrument_control.exe"
