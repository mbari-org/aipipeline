import numpy as np
import json
import tritonclient.http as httpclient

## Prequisites: pip install  --no-cache-dir  tritonclient[http]
## This script runs inference on the Google Multi-Species Whale Model using Triton Inference Server.

wav_path = "/Volumes/PAM_Analysis/GoogleMultiSpeciesWhaleModel2/resampled_24kHz_chunks/2018/04/MARS_20180413_065913_resampled_24kHz/MARS_20180413_065913_resampled_24kHz_chunk_002.wav"

# Read file as raw bytes
with open(wav_path, "rb") as f:
    wav_bytes = f.read()

data = np.frombuffer(wav_bytes, dtype=np.uint8)

triton = httpclient.InferenceServerClient(url="doris.shore.mbari.org:8080")

# Input (batch=1, length=N)
inp = httpclient.InferInput("WAV_DATA", [1, len(data)], "UINT8")
inp.set_data_from_numpy(data[np.newaxis, :])

# Output both SCORE and CLASS_NAME
outputs = [
    httpclient.InferRequestedOutput("SCORE"),
    httpclient.InferRequestedOutput("CLASS_NAME")
]

# Run inference
res = triton.infer(model_name="GoogleMultiSpeciesPipeline", inputs=[inp], outputs=outputs)
scores = res.as_numpy("SCORE")
classes = res.as_numpy("CLASS_NAME")
decoded_classes = [item.decode('utf-8') for item in classes]

# Format to 10 decimal places
print("SCORES :", np.array2string(scores, formatter={'float_kind':lambda x: f"{x:.10f}"}))
print("CLASS_NAME :", decoded_classes)

# Save the results to a JSON file
results = {
    "filenames": [wav_path],
    "scores": scores.tolist(),
    "class_names": decoded_classes
}
output_path = "MARS_20180413_065913_resampled_24kHz_chunk_002.json"
print(f"Saving results to {output_path}")
with open(output_path, "w") as f:
    json.dump(results, f, indent=4)

