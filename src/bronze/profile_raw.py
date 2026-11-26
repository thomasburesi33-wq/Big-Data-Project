#!/usr/bin/env python3
"""Profilage des données brutes (bronze) avec DuckDB : tout est lu en texte."""
import datetime
import os
import sys

import duckdb

CSV = sys.argv[1] if len(sys.argv) > 1 else "data/ecommerce_retail_transactions_raw.csv"
con = duckdb.connect()
con.execute(
    f"CREATE VIEW raw AS SELECT * FROM read_csv('{CSV}', header=true, "
    f"all_varchar=true, sample_size=-1)"
)


def q(sql):
    return con.execute(sql).fetchall()


print("=" * 72)
print(f"namespace={os.environ.get('KUBERNETES_NAMESPACE', '?')}  "
      f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
print(f"fichier : {CSV}")
total = q("SELECT count(*) FROM raw")[0][0]
cols = [r[0] for r in q("DESCRIBE raw")]
print(f"lignes : {total}   colonnes : {len(cols)}")
print("colonnes :", cols)

distinct_rows = q("SELECT count(*) FROM (SELECT DISTINCT * FROM raw)")[0][0]
print(f"doublons exacts (lignes en trop) : {total - distinct_rows}")

PLACEHOLDERS = "('n/a','na','null','none','nan','unknown','inconnu','?','-','--','missing')"

for c in cols:
    col = '"' + c.replace('"', '""') + '"'
    nulls, bidon, spaces, dist, minlen, maxlen, num_ok = q(f"""
        SELECT count(*) FILTER (WHERE {col} IS NULL OR trim({col}) = ''),
               count(*) FILTER (WHERE lower(trim({col})) IN {PLACEHOLDERS}),
               count(*) FILTER (WHERE {col} <> trim({col})),
               count(DISTINCT {col}),
               min(length({col})), max(length({col})),
               count(try_cast({col} AS DOUBLE))
        FROM raw""")[0]
    filled = total - nulls
    print(f"COLONNE {c}")
    print(f"  vides/NULL : {nulls} ({100 * nulls / total:.1f} %)   "
          f"valeurs bidons : {bidon}   espaces parasites : {spaces}")
    print(f"  distinctes : {dist}   longueur min/max : {minlen}/{maxlen}")

    if filled > 0 and num_ok >= 0.9 * filled:
        mn, mx, avg, neg, zero = q(f"""
            SELECT min(try_cast({col} AS DOUBLE)), max(try_cast({col} AS DOUBLE)),
                   avg(try_cast({col} AS DOUBLE)),
                   count(*) FILTER (WHERE try_cast({col} AS DOUBLE) < 0),
                   count(*) FILTER (WHERE try_cast({col} AS DOUBLE) = 0)
            FROM raw""")[0]
        print(f"  NUMÉRIQUE ({num_ok}/{filled} convertibles) : min={mn} max={mx} "
              f"moy={avg:.2f} négatifs={neg} zéros={zero}")
        if num_ok < filled:
            bad = q(f"""SELECT {col}, count(*) FROM raw
                        WHERE {col} IS NOT NULL AND try_cast({col} AS DOUBLE) IS NULL
                        GROUP BY 1 ORDER BY 2 DESC LIMIT 8""")
            print("  non convertibles :", bad)

    if dist <= 40:
        rows = q(f"SELECT {col}, count(*) n FROM raw GROUP BY 1 ORDER BY n DESC")
        print("  valeurs :", rows)
    else:
        pats = q(f"""
            SELECT regexp_replace(regexp_replace({col}, '[0-9]', '9', 'g'),
                                  '[A-Za-z]', 'A', 'g') AS motif, count(*) n
            FROM raw WHERE {col} IS NOT NULL GROUP BY 1 ORDER BY n DESC LIMIT 8""")
        print("  formats (9=chiffre, A=lettre) :", pats)
        ex = q(f"SELECT DISTINCT {col} FROM raw WHERE {col} IS NOT NULL LIMIT 5")
        print("  exemples :", [e[0] for e in ex])
