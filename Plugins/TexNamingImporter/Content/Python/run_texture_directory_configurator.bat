@echo off
setlocal EnableExtensions

rem === 設定値をここで指定してください ===
set "CONFIG_PATH=Config\TexNamingImporter\Config.json"
set "DIR_PATH=/Game/Textures"
set "EXTRA_FLAGS=--delete"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

for %%I in ("..\..\..\..") do set "PROJECT_ROOT=%%~fI"
set "PY_SCRIPT=%CD%\texture_directory_configurator.py"
set "UPROJECT=%PROJECT_ROOT%\TexImporterProject.uproject"

if not exist "%UPROJECT%" (
    echo [ERROR] Uproject not found: %UPROJECT%
    popd >nul
    exit /b 1
)

for %%I in ("%CONFIG_PATH%") do set "CONFIG_PATH=%%~fI"

if not defined UE_CMD_PATH (
    set "UE_CMD=UnrealEditor-Cmd.exe"
) else (
    set "UE_CMD=%UE_CMD_PATH%"
)

echo Config   : %CONFIG_PATH%
echo Directory: %DIR_PATH%
echo Flags    : %EXTRA_FLAGS%

"%UE_CMD%" "%UPROJECT%" -run=pythonscript -script="%PY_SCRIPT%" -- "%CONFIG_PATH%" "%DIR_PATH%" %EXTRA_FLAGS%
set "CODE=%errorlevel%"

popd >nul
exit /b %CODE%
