#!/bin/bash
echo "============================================"
echo " Building CAN Bus Monitor Executable"
echo "============================================"
echo

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

echo
echo "Building executable..."
echo

# Build using spec file
pyinstaller CANBusMonitor.spec

echo
if [ -f "dist/CANBusMonitor" ]; then
    echo "============================================"
    echo " BUILD SUCCESSFUL!"
    echo "============================================"
    echo
    echo "Executable location: dist/CANBusMonitor"
    echo
    echo "Note: PCAN drivers must be installed on target system"
    echo
else
    echo "============================================"
    echo " BUILD FAILED!"
    echo "============================================"
    echo "Please check the error messages above."
    echo
fi
