; Inno Setup 6 script — compile with build\build_windows.ps1 (needs ISCC.exe)
; https://jrsoftware.org/isinfo.php

#define MyAppName "YT Media Downloader"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "boyaloxer"
#define MyAppURL "https://github.com/boyaloxer/yt-wav-cutter"
#define MyAppExeName "YT Media Downloader.exe"

[Setup]
AppId={{A7C3E2B1-9D4F-4E8A-B2C1-5F6D8E9A0B12}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=..\dist
OutputBaseFilename=YT-Media-Downloader-Setup
SetupIconFile=..\assets\yt-wav-cutter.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checked

[Files]
; Entire PyInstaller onedir output (includes ffmpeg.exe after build script)
Source: "..\dist\YT Media Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
Filename: "https://nodejs.org/"; Description: "Open Node.js download (recommended for YouTube)"; Flags: postinstall shellexec skipifsilent unchecked

[Code]
function NodeExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{sys}\node.exe')) or
            FileExists(ExpandConstant('{pf64}\nodejs\node.exe')) or
            FileExists(ExpandConstant('{pf32}\nodejs\node.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\node\node.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not NodeExists() then
      MsgBox('Node.js was not detected.'#13#10#13#10 +
             'YouTube downloads work more reliably with Node.js installed.'#13#10 +
             'You can install the LTS build from https://nodejs.org/ after setup.',
             mbInformation, MB_OK);
  end;
end;
