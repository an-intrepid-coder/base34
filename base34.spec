# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['game.py'],
    pathex=[],
    binaries=[],
    datas=[["sansation/Sansation-Regular.ttf", "./sansation/"],
           ["window_icon.png", "."],
           ["images/Dude1.png", "./images/"],
           ["images/Dude2.png", "./images/"],
           ["images/Fog.png", "./images/"],
           ["images/Pillar1.png", "./images/"],
           ["images/Floor1.png", "./images/"],
           ["images/Outside.png", "./images/"],
           ["images/Tree1.png", "./images/"],
           ["images/Terminal.png", "./images/"],
           ["images/PatrolPath.png", "./images/"],
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='base34',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
