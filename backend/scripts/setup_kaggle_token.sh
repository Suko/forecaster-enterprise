#!/bin/bash
# Quick setup for Kaggle API token

echo "🔑 Setting up Kaggle API token..."
echo ""

# Get token from environment or prompt
if [ -z "$KAGGLE_API_TOKEN" ]; then
    echo "Enter your Kaggle API token (KGAT_...):"
    read -r KAGGLE_API_TOKEN
fi

# Get username
echo "Enter your Kaggle username:"
read -r KAGGLE_USERNAME

# Create kaggle.json
mkdir -p ~/.kaggle
cat > ~/.kaggle/kaggle.json << EOF
{
  "username": "$KAGGLE_USERNAME",
  "key": "$KAGGLE_API_TOKEN"
}
EOF

chmod 600 ~/.kaggle/kaggle.json

echo ""
echo "✅ Kaggle credentials saved to ~/.kaggle/kaggle.json"
echo ""
echo "Test with: kaggle competitions list"

