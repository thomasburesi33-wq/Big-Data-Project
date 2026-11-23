#!/usr/bin/env bash
# Enregistre la provenance du dataset dans data/SOURCE.txt.
# Usage : DATASET_LICENCE="..." [DOWNLOAD_DATE=AAAA-MM-JJ] ./src/bronze/make_source.sh
set -euo pipefail

DATASET_NAME="Messy E-Commerce Sales Dataset 2026"
DATASET_AUTHOR="afaqkhan091 (Kaggle)"
DATASET_URL="https://www.kaggle.com/datasets/afaqkhan091/messy-e-commerce-sales-dataset-2026"
DATASET_LICENCE="CC0: Public Domain"
DOWNLOAD_DATE="${DOWNLOAD_DATE:-$(date +%F)}"

FILE="data/ecommerce_retail_transactions_raw.csv"
BYTES=$(stat -c %s "$FILE")

{
  echo "nom           : $DATASET_NAME"
  echo "auteur        : $DATASET_AUTHOR"
  echo "dataset_url   : $DATASET_URL"
  echo "licence       : $DATASET_LICENCE"
  echo "telecharge_le : $DOWNLOAD_DATE"
  echo "fichier       : $(basename "$FILE")"
  echo "taille_octets : $BYTES"
  echo "taille_Mo     : $(awk "BEGIN{printf \"%.2f\", $BYTES/1048576}")"
  echo "lignes        : $(wc -l < "$FILE")"
  echo "sha256        : $(sha256sum "$FILE" | cut -d' ' -f1)"
  echo "verifie_le    : $(date '+%Y-%m-%d %H:%M:%S %Z') (namespace $KUBERNETES_NAMESPACE)"
} | tee data/SOURCE.txt

if [ "$BYTES" -lt 1048576 ] || [ "$BYTES" -gt 5242880 ]; then
  echo "ATTENTION : taille hors de la plage 1-5 Mo (pénalité de -1 point)"
else
  echo "OK : taille dans la plage 1-5 Mo"
fi
