# Kaggle API Setup Guide

**Purpose:** Set up Kaggle API to download M5 dataset

---

## Quick Setup

### Option 1: Using Environment Variable (Simplest)

```bash
export KAGGLE_API_TOKEN=KGAT_b9dd8c0191393945195d5258caa32780
```

Then run the download script - it will use the environment variable.

---

### Option 2: Using kaggle.json File

1. **Get your Kaggle username:**
   - Go to https://www.kaggle.com/account
   - Your username is in the URL or profile

2. **Create kaggle.json:**
   ```bash
   mkdir -p ~/.kaggle
   cat > ~/.kaggle/kaggle.json << EOF
   {
     "username": "YOUR_KAGGLE_USERNAME",
     "key": "KGAT_b9dd8c0191393945195d5258caa32780"
   }
   EOF
   chmod 600 ~/.kaggle/kaggle.json
   ```

3. **Replace `YOUR_KAGGLE_USERNAME`** with your actual Kaggle username

---

## Verify Setup

```bash
# Test authentication
kaggle competitions list
```

Should show list of competitions (not 401 error).

---

## Alternative: Download from Zenodo

If Kaggle API doesn't work, M5 dataset is also available on Zenodo:

1. **Download from Zenodo:**
   - URL: https://zenodo.org/records/12636070
   - Download: `m5-forecasting-accuracy.zip`

2. **Extract to:**
   ```
   backend/data/m5/
   ```

3. **Required files:**
   - `sales_train_evaluation.csv` (or `sales_train_validation.csv`)
   - `calendar.csv`

4. **Run script:**
   ```bash
   cd backend
   uv run python scripts/download_m5_data.py
   ```
   (It will skip download if files already exist)

---

## Troubleshooting

### Error: "401 Unauthorized"
- Check username is correct in kaggle.json
- Verify API token is valid
- Try using environment variable instead

### Error: "Could not find kaggle.json"
- Create `~/.kaggle/kaggle.json` file
- Or use `KAGGLE_API_TOKEN` environment variable

### Error: "ModuleNotFoundError: No module named 'kaggle'"
```bash
cd backend
uv add kaggle
```

---

*Guide created: 2025-12-08*

