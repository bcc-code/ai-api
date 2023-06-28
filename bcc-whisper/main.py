import json
import math
import os
import ssl
import torch
import whisper
import sys

from song_or_not.classifier import AudioClassifier
from song_or_not.inference import inference, load_model

ssl._create_default_https_context = ssl._create_unverified_context

SAMPLE_RATE = 16000
LENGTH = 5  # seconds
SAMPLES_PER_CHUNK = SAMPLE_RATE * LENGTH


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    model = load_model(device)
    model.eval()

    os.makedirs("out", exist_ok=True)

    arguments = sys.argv

    # transcribe specific file
    if len(arguments) > 1:
        file = arguments[1]
        out = arguments[2]
        if file.endswith(".wav"):
            transcribe_file(model, device, file, out)
    else:
        files = os.listdir("files")

        for file in files:
            if file.endswith(".wav"):
                transcribe_file(model, device, "files/" + file, "out/" + str.split(file, "/").pop() + ".json")


def transcribe_file(model, device: torch.device, file: str, out: str):
    res = inference(model, file, device, SAMPLE_RATE, SAMPLES_PER_CHUNK, LENGTH)

    current_type = "song"
    start = 0
    end = 0

    res2: list[tuple[str, int, int]] = []

    for x in res:
        d = x[1]
        # The sensitivity can be adjusted here a bit
        if d <= 2 or current_type == x[0]:
            end += d
        else:
            print(x)
            if current_type == "speech":
                res2.append((current_type, start * LENGTH, end * LENGTH))
            start = end
            end = end + x[1]
            current_type = x[0]

    if current_type == "speech":
        res2.append((current_type, start * LENGTH, end * LENGTH))

    audio = whisper.load_audio(file, SAMPLE_RATE)

    parts = []

    for r in res2:
        from_index = math.floor(r[1] * SAMPLE_RATE)
        to_index = math.floor(r[2] * SAMPLE_RATE)

        result = whisper.load_model("medium").transcribe(audio=audio[from_index:to_index], verbose=True)

        lines = []
        for segment in result["segments"]:
            lines.append({
                "start": segment["start"],  # type: ignore
                "end": segment["end"],  # type: ignore
                "text": segment["text"]  # type: ignore
            })

        parts.append({
            "start": r[1],
            "end": r[2],
            "transcription": lines,
        })

    f = open(out, "w")
    f.write(json.dumps(parts))
    f.close()


if __name__ == "__main__":
    main()
