#!/bin/bash
# Quick CLI test script
# Demonstrates: Load data -> Build tree -> Verify proof

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Testing Merkle Tree CLI with sample data..."
echo ""

python3 src/main.py <<EOF
1
1.2
10
0
2
2.1
2.2
0
4
4.1
0
4.2
0
0
0
EOF

echo ""
echo "Test complete!"
