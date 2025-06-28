# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Main_Gui.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('fatih.png', '.'), ('fatih_buton.png', '.'), ('fatıh.PNG', '.'), ('fk_icon.ico', '.'), ('logo.ico', '.'), ('logo.png', '.'), ('mail_logo.png', '.'), ('mailleri_tespit_et.png', '.'), ('google_maps_scraper.py', '.'), ('email_scraper.py', '.'), ('mail_sender.py', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='Main_Gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ReachSuiteIcon.ico'],
)
