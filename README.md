# Trading Intelligence

This repository contains scripts for data ingestion, feature engineering,
model training and optimization.

## Quantization Backend

`optimize.py` automatically selects a quantization backend based on the
engines available in `torch.backends.quantized.supported_engines`.
If `fbgemm` is supported it will be used; otherwise `qnnpack` is selected.
The chosen backend is printed when running the script.
