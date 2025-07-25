
#!/bin/bash

if [ -z "$1" ]; then
    echo "Uso: $0 [version_type]"
    echo "version_type: patch , minor, major"
else
    version_type="$1"
fi

gh workflow run "Create Release" -f version_type="$version_type"