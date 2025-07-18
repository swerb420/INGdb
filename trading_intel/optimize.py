import logging

import torch
import torch.nn.utils.prune as prune
import torch.quantization

from .config import LOG_FILE
from .modeling import SimpleLSTM

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)

state = torch.load("lstm.pth")
model = SimpleLSTM(input_dim=3)
model.load_state_dict(state)

prune.l1_unstructured(model.lstm, name="weight_ih_l0", amount=0.5)
prune.remove(model.lstm, "weight_ih_l0")

model.eval()
supported = torch.backends.quantized.supported_engines
backend = "fbgemm" if "fbgemm" in supported else "qnnpack"
torch.backends.quantized.engine = backend
print(f"Using quantization backend: {backend}")
model.qconfig = torch.quantization.get_default_qconfig(backend)
model_prepared = torch.quantization.prepare(model)
model_prepared(torch.randn(1, 1, 3))
model_int8 = torch.quantization.convert(model_prepared)

dummy = torch.randn(1, 1, 3)
torch.onnx.export(model_int8, dummy, "lstm_model.onnx", opset_version=13)
logger.info("\u2705 ONNX export complete.")
