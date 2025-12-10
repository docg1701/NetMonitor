#!/bin/bash

# Configuration
APP_NAME="NetMonitor"
APP_DESCRIPTION="Network Latency Monitoring Tool"
APP_CATEGORY="Network;Monitor;Internet;"
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"

TARGET_APP_IMAGE="$INSTALL_DIR/$APP_NAME.AppImage"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"
ICON_PATH="$ICON_DIR/$APP_NAME.png"

function uninstall() {
    echo "Uninstalling $APP_NAME..."
    
    if [ -f "$DESKTOP_FILE" ]; then
        rm "$DESKTOP_FILE"
        echo "-> Removed desktop entry: $DESKTOP_FILE"
    else
        echo "-> Desktop entry not found."
    fi

    if [ -f "$TARGET_APP_IMAGE" ]; then
        rm "$TARGET_APP_IMAGE"
        echo "-> Removed AppImage: $TARGET_APP_IMAGE"
    else
        echo "-> AppImage not found."
    fi

    if [ -f "$ICON_PATH" ]; then
        rm "$ICON_PATH"
        echo "-> Removed Icon: $ICON_PATH"
    else
        echo "-> Icon not found."
    fi

    update-desktop-database "$DESKTOP_DIR" 2>/dev/null
    echo "Uninstallation complete."
}

function install() {
    APP_IMAGE_PATH=$(realpath "$1")

    if [ ! -f "$APP_IMAGE_PATH" ]; then
        echo "Error: File not found at $APP_IMAGE_PATH"
        exit 1
    fi

    echo "Installing $APP_NAME..."

    # Create directories if they don't exist
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"

    # Copy AppImage to install directory
    cp "$APP_IMAGE_PATH" "$TARGET_APP_IMAGE"
    chmod +x "$TARGET_APP_IMAGE"
    echo "-> AppImage copied to $TARGET_APP_IMAGE"

    # Extract Icon from AppImage
    echo "-> Extracting icon..."
    cd /tmp
    "$TARGET_APP_IMAGE" --appimage-extract .DirIcon > /dev/null 2>&1
    if [ -f "squashfs-root/.DirIcon" ]; then
        mv squashfs-root/.DirIcon "$ICON_PATH"
        rm -rf squashfs-root
        echo "-> Icon extracted to $ICON_PATH"
    else
        # Fallback if extraction fails
        echo "-> Warning: Could not extract icon. Using generic network icon."
        ICON_PATH="network-workgroup" 
    fi

    # Create .desktop file
    # Note: WEBKIT_DISABLE_COMPOSITING_MODE=1 fixes blank screen on some systems
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=$APP_DESCRIPTION
Exec=env WEBKIT_DISABLE_COMPOSITING_MODE=1 "$TARGET_APP_IMAGE"
Icon=$ICON_PATH
Categories=$APP_CATEGORY
Terminal=false
StartupNotify=true
X-GNOME-UsesNotifications=true
EOF

    chmod +x "$DESKTOP_FILE"
    echo "-> Desktop entry created at $DESKTOP_FILE"

    # Update desktop database
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null

    echo "Success! $APP_NAME has been added to your menu under Internet."
}

# Main Logic
if [ "$1" == "--uninstall" ] || [ "$1" == "-u" ] || [ "$1" == "uninstall" ]; then
    uninstall
elif [ -n "$1" ]; then
    install "$1"
else
    echo "NetMonitor Installer/Uninstaller"
    echo ""
    echo "Usage:"
    echo "  Install:   $0 <path-to-NetMonitor.AppImage>"
    echo "  Uninstall: $0 --uninstall"
    echo ""
    echo "Example:"
    echo "  $0 ./NetMonitor_1.0.0_amd64.AppImage"
    exit 1
fi