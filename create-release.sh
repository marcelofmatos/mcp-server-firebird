
#!/bin/bash

if [ -z "$1" ]; then
    echo "Uso: $0 [version_type]"
    echo "version_type: patch , minor, major"
    exit 1
fi

version_type="$1"
gh workflow run "Create Release" -f version_type="$version_type"

