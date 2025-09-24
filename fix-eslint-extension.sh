#!/bin/bash

# Fix ESLint Extension Corruption
# This script reinstalls the corrupted ESLint extension

echo "Fixing ESLint extension corruption..."

# Remove the corrupted extension
rm -rf ~/.vscode/extensions/dbaeumer.vscode-eslint*

echo "Removed corrupted ESLint extension."

# Install ESLint extension via command line
# Note: This requires VSCode CLI tools to be installed
# If code command is available, use it to install
if command -v code &> /dev/null; then
    echo "Installing ESLint extension..."
    code --install-extension dbaeumer.vscode-eslint
    echo "ESLint extension installed successfully."
else
    echo "VSCode CLI not found. Please manually reinstall the ESLint extension:"
    echo "1. Open VSCode"
    echo "2. Go to Extensions (Ctrl+Shift+X)"
    echo "3. Search for 'ESLint' by Dirk Baeumer"
    echo "4. Uninstall if present, then install again"
    echo "5. Reload VSCode window"
fi

echo "ESLint extension fix completed."