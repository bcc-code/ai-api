import argparse
import json
import math
import ssl
import torch
import whisper

from inference import load_model, inference, AudioClassifier

ssl._create_default_https_context = ssl._create_unverified_context

SAMPLE_RATE = 16000
LENGTH = 5  # seconds
SAMPLES_PER_CHUNK = SAMPLE_RATE * LENGTH


def parse_arguments():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--language", help="language", default="no")
    parser.add_argument("-m", "--model", help="whisper model to use", default="medium")
    parser.add_argument("src", help="source file")
    parser.add_argument("output", help="output file")

    return parser.parse_args()


def main():
    # import for side effects
    _ = AudioClassifier
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    config = vars(parse_arguments())
    file = config["src"]
    out = config["output"]
    language = config["language"]
    model = config["model"]
    transcribe_file(device, file, out, language, model)


def transcribe_file(device: torch.device, file: str, out: str, language: str, model: str):
    detection_model = load_model(device)
    detection_model.eval()
    res = inference(detection_model, file, device, SAMPLE_RATE, SAMPLES_PER_CHUNK, LENGTH)

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

    parts = {
        "text": "",
        "segments": [],
        "language": language,
    }

    for r in res2:
        from_index = math.floor(r[1] * SAMPLE_RATE)
        to_index = math.floor(r[2] * SAMPLE_RATE)

        result = whisper.load_model(model) \
            .transcribe(audio=audio[from_index:to_index],
                        verbose=True,
                        language=language)

        if parts["text"] != "":
            parts["text"] += "\n\n"

        parts["text"] += result["text"]

        for segment in result["segments"]:
            segment["start"] += r[1]
            segment["end"] += r[1]
            parts["segments"].append(segment)

    f = open(out, "w")
    f.write(json.dumps(parts))
    f.close()


if __name__ == "__main__":
    main()
