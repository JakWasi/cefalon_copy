#!/bin/bash

set -e

DATA_DIR="../data"
RAW_DIR="$DATA_DIR/raw_pcaps"
FLOWS_DIR="$DATA_DIR/flows"
CAPTURES_DIR="$DATA_DIR/captures"

mkdir -p "$RAW_DIR" "$FLOWS_DIR" "$CAPTURES_DIR"

echo "[+] Downloading datasets to $DATA_DIR"
echo ""

#############################################
# UNSW-NB15 (manual download required)
#############################################
echo "[*] UNSW-NB15 cannot be downloaded automatically (401 auth)."
echo "[*] Please download manually from:"
echo "    https://research.unsw.edu.au/projects/unsw-nb15-dataset"
echo ""

mkdir -p "$DATA_DIR/UNSW-NB15"
touch "$DATA_DIR/UNSW-NB15/README_MANUAL_DOWNLOAD.txt"
echo "Download UNSW-NB15 manually and extract here." \
    > "$DATA_DIR/UNSW-NB15/README_MANUAL_DOWNLOAD.txt"

#############################################
# CICIDS2017 – Flow CSV
#############################################
echo "[*] Downloading CICIDS2017 FLows..."
mkdir -p "$DATA_DIR/CICIDS2017"
cd "$DATA_DIR/CICIDS2017"

wget -nc https://www.unb.ca/cic/datasets/ids-2017/CICIDS2017.csv.gz || {
    echo "[-] Could not download CICIDS2017 automatically."
    echo "    Download manually from:"
    echo "    https://www.unb.ca/cic/datasets/ids-2017.html"
}

echo "[*] Extracting CICIDS2017..."
gunzip -f CICIDS2017.csv.gz 2>/dev/null || true

cd - >/dev/null


#############################################
# MAWI Traffic
#############################################
echo "[*] Downloading MAWI 2019 dataset..."
mkdir -p "$DATA_DIR/MAWI"
cd "$DATA_DIR/MAWI"

wget -nc http://mawi.wide.ad.jp/mawi/samplepoint-F/2019/201908011400.pcap.gz

echo "[*] Extracting MAWI..."
gunzip -kf 201908011400.pcap.gz

mv -f 201908011400.pcap "$RAW_DIR" 2>/dev/null || true

cd - >/dev/null


#############################################
# CTU-13 Botnet Traffic
#############################################
echo "[*] Downloading CTU-13..."
mkdir -p "$DATA_DIR/CTU13"
cd "$DATA_DIR/CTU13"

wget -nc https://mcfp.felk.cvut.cz/publicDatasets/CTU-13/CTU-13-Dataset.tar.gz

echo "[*] Extracting CTU-13..."
tar -xzf CTU-13-Dataset.tar.gz

# Move pcaps to the global raw directory
find . -name "*.pcap" -exec mv "{}" "$RAW_DIR" \;

cd - >/dev/null


echo ""
echo "[+] Download completed successfully!"
echo "[+] Raw PCAPs stored in: $RAW_DIR"
echo "[+] CSV flow datasets stored in: $FLOWS_DIR / dataset folders"
echo "[+] UNSW-NB15 must be downloaded manually."
