# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['speech_to_text_gui.py'],
    pathex=[],
    binaries=[('C:\\Users\\Administrator\\Documents\\trae_projects\\yy\\.venv\\lib\\site-packages\\vosk\\*.dll', '.')],
    datas=[('vosk_model', 'vosk_model')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='语音转文字_修复版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='语音转文字_修复版',
)
