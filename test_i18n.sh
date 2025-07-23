#!/bin/bash
# Test script for i18n functionality

echo "🌍 Testing Firebird Expert MCP Server Internationalization"
echo "========================================================="

# Test English (default)
echo ""
echo "🇺🇸 Testing English (en_US)..."
export FIREBIRD_LANGUAGE=en_US
timeout 3s python3 server.py &
SERVER_PID=$!
sleep 2
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo ""
echo "🇧🇷 Testing Portuguese (pt_BR)..."
export FIREBIRD_LANGUAGE=pt_BR  
timeout 3s python3 server.py &
SERVER_PID=$!
sleep 2
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo ""
echo "🌍 Testing fallback (non-existent language)..."
export FIREBIRD_LANGUAGE=fr_FR
timeout 3s python3 server.py &
SERVER_PID=$!
sleep 2
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo ""
echo "✅ i18n testing completed!"
echo ""
echo "Available languages:"
echo "  • en_US (English)"
echo "  • pt_BR (Português)"
echo ""
echo "Usage:"
echo "  export FIREBIRD_LANGUAGE=pt_BR && python3 server.py"
echo "  export FIREBIRD_LANGUAGE=en_US && python3 server.py"
