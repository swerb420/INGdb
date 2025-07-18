# Trading Intelligence

This repository contains scripts for data ingestion, feature engineering,
model training and optimization.

## Quantization Backend

`optimize.py` automatically selects a quantization backend based on the
engines available in `torch.backends.quantized.supported_engines`.
If `fbgemm` is supported it will be used; otherwise `qnnpack` is selected.
The chosen backend is printed when running the script.

This project ingests price and social sentiment data, builds features, trains a model and exposes an inference loop.

## Setup
1. Install Python 3 and `pip`.
2. Install the package in editable mode along with dependencies:
   ```bash
   pip install -e .
   ```
3. Configure environment variables. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with values for:
   - `DATABASE_URL`
   - `ALPHA_VANTAGE_API_KEY`
   - `FRED_API_KEY`
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`

## Usage
### Ingestion
Downloads crypto, stock, on-chain and reddit data and writes them to the database:
```bash
python trading_intel/ingestion.py
```

### Feature Generation
Creates engineered features from the ingested data:
```bash
python trading_intel/features.py
```

### Training
Trains a simple LSTM on the generated features and saves `lstm.pth`:
```bash
python trading_intel/modeling.py
```

### Optimization
Prunes and quantizes the model and exports `lstm_model.onnx`:
```bash
python trading_intel/optimize.py
```

### Inference
Runs an hourly loop of data ingestion, feature creation and ONNX inference:
```bash
python trading_intel/inference.py
```
You can also schedule this loop via the CLI. After installing the package in
editable mode with `pip install -e .`, use the `ti-cli` entry point:
```bash
ti-cli start    # add to crontab
ti-cli stop     # remove from crontab
ti-cli status   # show current crontab
```

## Development

### Formatting
Run `pre-commit` to automatically format and lint the code:

```bash
pre-commit run --all-files
```

### Testing
Execute the unit tests with `pytest`:

```bash
pytest
```

