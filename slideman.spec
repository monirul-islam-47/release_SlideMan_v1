# slideman.spec
# -*- mode: python -*-
import sys, os, glob
from PyInstaller.utils.hooks import (
    collect_dynamic_libs,
    collect_submodules
)

# Path definitions
base_dir = os.path.abspath('.')
src_dir = os.path.join(base_dir, 'src')

# Data files collection - more explicit approach
datas = []

# Add icon files
icon_dir = os.path.join(base_dir, 'resources', 'icons')
for icon_file in glob.glob(os.path.join(icon_dir, '*.*')):
    datas.append((icon_file, os.path.join('resources', 'icons')))

# Add QSS style files
qss_dir = os.path.join(base_dir, 'resources', 'qss')
for qss_file in glob.glob(os.path.join(qss_dir, '*.*')):
    datas.append((qss_file, os.path.join('resources', 'qss')))

# Add resource.qrc file
resource_qrc = os.path.join(base_dir, 'resources', 'resources.qrc')
if os.path.exists(resource_qrc):
    datas.append((resource_qrc, 'resources'))

# PySide6 binaries
binaries = collect_dynamic_libs('PySide6')

# Python-pptx and other dependencies
hiddenimports = collect_submodules('pptx') + collect_submodules('PySide6') + [
    "lxml._elementpath",
    "PIL",
    "appdirs",
    "sqlite3",
    "rapidfuzz",
    # Additional PySide6 modules
    "PySide6.QtWidgets",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtSql"
]

a = Analysis(
    ['main.py'],
    pathex=[base_dir, src_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hooksconfig={
        'pyside6': {
            'modules': [
                'QtWidgets',
                'QtCore', 
                'QtGui',
                'QtSql'
            ]
        }
    },
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SLIDEMan',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Use a default icon from resources if available
    icon=os.path.join(icon_dir, 'cil-mood-good.png') if os.path.exists(os.path.join(icon_dir, 'cil-mood-good.png')) else None
)
