@echo off
echo ============================================
echo  Building CAN Bus Monitor Executable
echo ============================================
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building executable...
echo.

REM Build using spec file
pyinstaller CANBusMonitor.spec

echo.
if exist dist\CANBusMonitor.exe (
    echo ============================================
    echo  BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo Executable location: dist\CANBusMonitor.exe
    echo.
    echo Note: PCAN drivers must be installed on target PC
    echo Download from: https://www.peak-system.com/
    echo.
) else (
    echo ============================================
    echo  BUILD FAILED!
    echo ============================================
    echo Please check the error messages above.
    echo.
)

pause
