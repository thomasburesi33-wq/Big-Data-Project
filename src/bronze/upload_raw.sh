#!/usr/bin/env bash
# Dépose le CSV brut sur S3 (bronze) sans le modifier, puis vérifie l'intégrité.
set -euo pipefail

FILE="${1:-data/ecommerce_retail_transactions_raw.csv}"
BUCKET="${LAB_BUCKET_NAME:-$KUBERNETES_NAMESPACE}"
KEY="bronze/$(basename "$FILE")"

echo "== Contexte =="
echo "namespace : $KUBERNETES_NAMESPACE"
echo "date      : $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "fichier   : $FILE ($(stat -c %s "$FILE") octets)"

echo "== Dépôt =="
aws s3 --profile 'default' cp "$FILE" "s3://$BUCKET/$KEY"

echo "== Vérification d'intégrité (sha256) =="
LOCAL=$(sha256sum "$FILE" | cut -d' ' -f1)
REMOTE=$(aws s3 --profile 'default' cp "s3://$BUCKET/$KEY" - | sha256sum | cut -d' ' -f1)
echo "local  : $LOCAL"
echo "remote : $REMOTE"
[ "$LOCAL" = "$REMOTE" ] && echo "OK : fichier identique" || { echo "ERREUR : différence"; exit 1; }
