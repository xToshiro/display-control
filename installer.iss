[Setup]
AppName=AOC Display Control Panel
AppVersion=1.3.0
DefaultDirName={localappdata}\DisplayControl
DefaultGroupName=AOC Display Control Panel
UninstallDisplayIcon={app}\DisplayControl.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=DisplayControlSetup
SetupIconFile=app_icon.ico
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\DisplayControl.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\AOC Display Control Panel"; Filename: "{app}\DisplayControl.exe"
Name: "{userdesktop}\AOC Display Control Panel"; Filename: "{app}\DisplayControl.exe"

[Run]
Filename: "{app}\DisplayControl.exe"; Description: "Iniciar AOC Display Control Panel"; Flags: nowait postinstall skipifsilent
