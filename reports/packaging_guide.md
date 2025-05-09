# Complete Guide: Packaging SlideMan (PySide6) for Windows

This guide documents the process we used to package the SlideMan application (Python/PySide6) into a standalone Windows executable and installer.

## 1. PREREQUISITES

### 1.1. Required Tools
- Python 3.9+
- Poetry (package management)
- PyInstaller (creating the executable)
- Inno Setup (creating the installer)

### 1.2. Setup Environment
```powershell
# Activate virtual environment
.\venv\Scripts\activate
```

### 1.3. Install PyInstaller
```powershell
# Add PyInstaller as a dev dependency
poetry add --dev pyinstaller
```

## 2. CREATE ENTRY POINT

### 2.1. Create `main.py` in Project Root
```python
#!/usr/bin/env python
# main.py - Entry point for SlideMan application
import os
import sys

# Add resource_path helper for PyInstaller
def resource_path(rel_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, rel_path)

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

if __name__ == "__main__":
    # Import and run the main function from slideman.__main__
    from slideman.__main__ import main
    main()
```

## 3. CREATE PYINSTALLER SPEC FILE

### 3.1. Define PyInstaller Configuration
```python
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
```

## 4. CREATE INNO SETUP SCRIPT

### 4.1. Define Installer Configuration
```ini
; slideman.iss
[Setup]
AppName=SlideMan
AppVersion=1.0.0
DefaultDirName={autopf}\SlideMan
DefaultGroupName=SlideMan
OutputBaseFilename=SlideMan_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\SLIDEMan.exe

[Files]
Source: "dist\SLIDEMan.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SLIDEMan"; Filename: "{app}\SLIDEMan.exe"
Name: "{group}\Uninstall SLIDEMan"; Filename: "{uninstallexe}"
Name: "{userdesktop}\SLIDEMan"; Filename: "{app}\SLIDEMan.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\SLIDEMan.exe"; Description: "Launch SLIDEMan"; Flags: nowait postinstall skipifsilent
```

## 5. BUILD THE EXECUTABLE

### 5.1. Run PyInstaller
```powershell
# Build the executable from the spec file
pyinstaller slideman.spec
```

This builds the following:
- `dist/SLIDEMan.exe` (standalone executable, ~215MB)

### 5.2. Verify the Build
```powershell
# Check that the executable was created
dir dist
```

## 6. CREATE THE INSTALLER

### 6.1. Install Inno Setup
- Download and install from: https://jrsoftware.org/isdl.php

### 6.2. Compile the Installer
Two options:

#### Option A: GUI Method
- Open Inno Setup Compiler
- File > Open > select slideman.iss
- Build > Compile

#### Option B: Command Line (if ISCC is in PATH)
```powershell
# Compile the installer from the command line
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" slideman.iss
```

This creates:
- `Output/SlideMan_Setup.exe` (installer)

## 7. KEY FEATURES IN OUR IMPLEMENTATION

### 7.1. Resource Path Helper
```python
def resource_path(rel_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, rel_path)
```
- Ensures resources are found in both development and bundled environments
- Works with PyInstaller's `_MEIPASS` temporary directory

### 7.2. PyInstaller Spec Features
- Explicit resource gathering with glob
- PySide6 module dependencies explicitly included
- Hidden imports for key libraries (pptx, lxml)
- Single-file build for easy distribution

### 7.3. Inno Setup Script Features
- Low privilege installation (non-admin)
- Option for desktop icon creation
- Custom branding and naming
- Auto-launch option

## 8. TESTING THE APPLICATION

1. Deploy to a clean Windows machine without Python
2. Run the installer: `SlideMan_Setup.exe`
3. Verify all app features work:
   - Drag-and-drop in assembly/delivery pages (as noted in project memory)
   - Keyword management functionality
   - All UI elements and styling
   - File operations

## 9. TROUBLESHOOTING TIPS

- If resources don't load: Check `resource_path` implementation
- Missing modules: Add to `hiddenimports` list in spec file
- SQLite issues: Verify SQLite3 is properly bundled
- UI rendering problems: Check Qt plugins in the spec
