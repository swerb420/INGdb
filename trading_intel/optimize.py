import logging
from pathlib import Path

import torch
import torch.nn.utils.prune as prune
import torch.quantization

from .logging_utils import setup_logging
from .modeling import SimpleLSTM

logger = logging.getLogger(__name__)

base_dir = Path(__file__).resolve().parent
state = torch.load(base_dir / "lstm.pth")
model = SimpleLSTM(input_dim=3)
model.load_state_dict(state)

prune.l1_unstructured(model.lstm, name="weight_ih_l0", amount=0.5)
prune.remove(model.lstm, "weight_ih_l0")

model.eval()
supported = torch.backends.quantized.supported_engines
backend = "fbgemm" if "fbgemm" in supported else "qnnpack"
torch.backends.quantized.engine = backend
logger.info("Using quantization backend: %s", backend)
model.qconfig = torch.quantization.get_default_qconfig(backend)
model_prepared = torch.quantization.prepare(model)
model_prepared(torch.randn(1, 1, 3))
model_int8 = torch.quantization.convert(model_prepared)

dummy = torch.randn(1, 1, 3)
torch.onnx.export(
    model_int8,
    dummy,
    base_dir / "lstm_model.onnx",
    opset_version=13,
)
logger.info("\u2705 ONNX export complete.")
