# Data Sources

This document records where RetailIQ's data comes from and how to verify it.
Raw data files are **not** stored in this repository (see `.gitignore`).

---

## Source

| Item | Value |
|---|---|
| Dataset | Walmart M5 Forecasting – Accuracy (Kaggle competition) |
| URL | https://www.kaggle.com/competitions/m5-forecasting-accuracy/data |
| Archive | `m5-forecasting-accuracy.zip` |
| Archive size | 48,009,163 bytes |
| Archive SHA-256 | `0349ba38a2efd30d0f5acc6394c1110e140e1a990c650d7b5ca44c5b25dd12f5` |
| Downloaded | 2026-11-17, via the Kaggle website ("Download All") |
| Integrity test | `unzip -t` — no errors detected |

Kaggle does not publish official checksums for this archive. The SHA-256
values below identify the exact copy used in this project, so any later
change to the files can be detected.

---

## Files in `data/raw/`

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `calendar.csv` | 103,469 | `d12b5914ef03e66649adf5dd9e996e6602251c22b7a6af8f1f7e3aa12f8860f5` |
| `sales_train_evaluation.csv` | 121,736,518 | `4b4a47c44c38380d2a9168216fea8c9ff2f31b1ddb772f8a0995952a038b8aa0` |
| `sales_train_validation.csv` | 120,007,726 | `f368e66ed1dbecb48b2cc8fc589bf68b3deddbbb36bf5c88b4d6d0a09b9b6724` |
| `sample_submission.csv` | 5,228,786 | `eb7597afbec367475ef25dc6dbbc009b8faa47fa2107252c72a029e3cdf72343` |
| `sell_prices.csv` | 203,395,785 | `9da3ad1f8b8ccacdbdc70612191dd375ec24a4ac6625c24b75b3bc60b0bed2ef` |

Row counts, columns, and data quality results are recorded separately after
validation (see `docs/data_validation.md`, to be created).

---

## Rules

- Files in `data/raw/` are never edited. All cleaning and reshaping happens
  in code and writes to `data/processed/`.
- Every transformation is documented in `docs/data_transformations.md`.

---

## How to Obtain the Data

1. Sign in to Kaggle and open the URL above.
2. Accept the competition rules (required by Kaggle before downloading).
3. Click **Download All** to get `m5-forecasting-accuracy.zip`.
4. From the project folder, extract into `data/raw/` without overwriting:

   ```bash
   unzip -n ~/Downloads/m5-forecasting-accuracy.zip -d data/raw/
   ```

5. Verify the files match the checksums above:

   ```bash
   cd data/raw && shasum -a 256 *.csv
   ```

Use of the data is subject to Kaggle's competition rules.
