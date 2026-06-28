import lightgbm as lgb
from onnxmltools import convert_lightgbm
from onnxmltools.convert.common.data_types import FloatTensorType
import os

def convert_model():
    print("Loading LightGBM model...")
    model_path = "saved_models/m-8a7257ac0857427e9daa6ba9105c4f56/artifacts/model.lgb"
    lgb_model = lgb.Booster(model_file=model_path)

    # Determine number of features to specify input shape
    num_features = lgb_model.num_feature()
    initial_types = [('input', FloatTensorType([None, num_features]))]

    print(f"Converting model with {num_features} features to ONNX...")
    # Convert model to ONNX
    onnx_model = convert_lightgbm(lgb_model, initial_types=initial_types)

    # Save ONNX model in the same artifacts directory
    onnx_path = "saved_models/m-8a7257ac0857427e9daa6ba9105c4f56/artifacts/model.onnx"
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
    print(f"ONNX model saved successfully to {onnx_path}")

if __name__ == "__main__":
    convert_model()
