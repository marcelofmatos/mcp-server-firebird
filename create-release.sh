
#!/bin/bash

case "$1" in
    patch|minor|major)
        version_type="$1"
        ;;
    *)
        echo "Opção inválida: $1"
        echo "As opções válidas são: patch, minor, major"
        exit 1
        ;;
esac

gh workflow run "Create Release" -f version_type="$version_type"

