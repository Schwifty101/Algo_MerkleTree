#!/bin/bash
# Manual download helper for Amazon Review Datasets
# Since the server may be slow/timing out, use wget or curl with resume capability

echo "=========================================="
echo "Amazon Review Dataset Download Helper"
echo "=========================================="
echo ""
echo "The automatic Python downloader may timeout on large files."
echo "This script uses wget/curl with retry and resume capabilities."
echo ""

# Check for wget or curl
if command -v wget &> /dev/null; then
    DOWNLOADER="wget"
    echo "✓ Found wget"
elif command -v curl &> /dev/null; then
    DOWNLOADER="curl"
    echo "✓ Found curl"
else
    echo "❌ Neither wget nor curl found. Please install one of them."
    exit 1
fi

# Create data directory
mkdir -p data/raw
cd data/raw

echo ""
echo "Available datasets (5-core versions with 1M+ reviews):"
echo "1. Electronics (6.7M reviews) - 850 MB compressed"
echo "2. Books (27M reviews) - 3.5 GB compressed"
echo "3. Home_and_Kitchen (6.9M reviews) - 900 MB compressed"
echo "4. Clothing_Shoes_and_Jewelry (11M reviews) - 1.4 GB compressed"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        DATASET="Electronics"
        URL="http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Electronics_5.json.gz"
        ;;
    2)
        DATASET="Books"
        URL="http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Books_5.json.gz"
        ;;
    3)
        DATASET="Home_and_Kitchen"
        URL="http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Home_and_Kitchen_5.json.gz"
        ;;
    4)
        DATASET="Clothing_Shoes_and_Jewelry"
        URL="http://deepyeti.ucsd.edu/jianmo/amazon/categoryFilesSmall/Clothing_Shoes_and_Jewelry_5.json.gz"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

FILENAME="${DATASET}_5.json.gz"
OUTPUT="${DATASET}_5.json"

echo ""
echo "Downloading $DATASET dataset..."
echo "URL: $URL"
echo "This may take 5-30 minutes depending on your connection..."
echo ""

if [ "$DOWNLOADER" = "wget" ]; then
    # wget with resume capability and timeout
    wget -c --timeout=30 --tries=10 -O "$FILENAME" "$URL"
else
    # curl with resume capability
    curl -C - --connect-timeout 30 --max-time 3600 -o "$FILENAME" "$URL"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Download complete!"
    echo ""
    
    # Check if file exists and decompress
    if [ -f "$FILENAME" ]; then
        FILE_SIZE=$(du -h "$FILENAME" | cut -f1)
        echo "Compressed file size: $FILE_SIZE"
        echo ""
        echo "Decompressing..."
        
        gunzip -c "$FILENAME" > "$OUTPUT"
        
        if [ $? -eq 0 ]; then
            echo "✓ Decompression complete!"
            UNCOMPRESSED_SIZE=$(du -h "$OUTPUT" | cut -f1)
            echo "Uncompressed file size: $UNCOMPRESSED_SIZE"
            
            # Count reviews
            echo ""
            echo "Counting reviews (this may take a moment)..."
            REVIEW_COUNT=$(wc -l < "$OUTPUT")
            echo "Total reviews: $(printf "%'d" $REVIEW_COUNT)"
            
            echo ""
            echo "✓ Dataset ready at: data/raw/$OUTPUT"
            echo ""
            
            # Ask if user wants to delete compressed file
            read -p "Delete compressed file to save space? (y/n): " delete_choice
            if [ "$delete_choice" = "y" ] || [ "$delete_choice" = "Y" ]; then
                rm "$FILENAME"
                echo "✓ Compressed file deleted"
            fi
        else
            echo "❌ Decompression failed"
            exit 1
        fi
    else
        echo "❌ Download failed - file not found"
        exit 1
    fi
else
    echo ""
    echo "❌ Download failed"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check your internet connection"
    echo "2. The server might be down - try again later"
    echo "3. Try downloading manually from: https://nijianmo.github.io/amazon/index.html"
    echo "4. Alternative: Use a download manager (IDM, aria2c, etc.)"
    exit 1
fi

echo ""
echo "=========================================="
echo "Next steps:"
echo "1. Run: python download_and_test.py"
echo "2. Or run: python src/main.py"
echo "=========================================="
