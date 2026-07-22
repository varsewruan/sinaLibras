; Instalador do SINALibras (Inno Setup 6).
;
; Empacota a saída onedir do PyInstaller (dist\SINALibras\) num único
; SINALibras-setup.exe — o arquivo que se manda pra alguém instalar.
;
; Compilar (depois do pyinstaller, a partir de desktop/):
;   & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
;
; Saída: desktop\dist\installer\SINALibras-setup.exe

#define MyAppName "SINALibras"
#define MyAppVersion "1.0.0"
#define MyAppExeName "SINALibras.exe"

[Setup]
AppId={{9F2B4C1E-7A3D-4E58-9B6F-2C8D1A5E4F70}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=SINALibras
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Sem página "escolha a pasta": pra quem só quer instalar e jogar, ela é uma
; decisão a mais sem consequência. O caminho padrão serve.
DisableDirPage=yes
DisableProgramGroupPage=yes

; PrivilegesRequired=lowest instala em %LOCALAPPDATA%\Programs sem pedir UAC.
; Com admin o Windows mostraria o prompt de elevação logo depois do aviso do
; SmartScreen — dois sustos seguidos num app não assinado. Instalação por
; usuário também casa com o app gravar dados em %LOCALAPPDATA%.
PrivilegesRequired=lowest

; O mongod embutido é x64; num Windows 32 bits o app não roda.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

OutputDir=dist\installer
OutputBaseFilename=SINALibras-setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; lzma2/max + solid: são ~250 MB de payload, quase tudo texto (runtime Python)
; e binário comprimível. Vale o tempo extra de compressão pra encolher o que
; alguém precisa baixar.
Compression=lzma2/max
SolidCompression=yes

WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
; Recursivo: a saída onedir do PyInstaller tem _internal\ com o runtime Python,
; o mongod e os assets dos sinais.
Source: "dist\SINALibras\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir o {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; A janela do app é um perfil de Chromium criado em runtime, fora do controle
; do instalador; sem isso a pasta {app} sobra depois de desinstalar.
Type: filesandordirs; Name: "{app}"

; Nota: os dados do usuário (banco, streak, conquistas) ficam em
; %LOCALAPPDATA%\SINALibras e são preservados de propósito na desinstalação —
; reinstalar não deve zerar o progresso de quem já jogou. Pra apagar de vez,
; apagar essa pasta à mão.
