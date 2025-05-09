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
UninstallDisplayIcon={app}\SlideMan.exe

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
