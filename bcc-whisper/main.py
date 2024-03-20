import argparse
import json
import math
import ssl
import torch
import whisper_timestamped as whisper
import os
import datetime

from inference import load_model, inference, AudioClassifier

# noinspection PyProtectedMember
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

    # start and end are in chunks / segments. So timestamp is start * LENGTH and end * LENGTH
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

    loaded_model = whisper.load_model(model)

    current_language = language
    for r in res2:
        from_index = math.floor(r[1] * SAMPLE_RATE)
        to_index = math.floor(r[2] * SAMPLE_RATE)

        if language == "" or language == "auto":
            # detect the spoken language
            mel = (whisper.log_mel_spectrogram(whisper.pad_or_trim(audio[from_index:to_index]))
                   .to(loaded_model.device))
            _, probs = loaded_model.detect_language(mel)
            current_language = max(probs, key=probs.get)
            print(f"Detected language: {current_language}")

        result = whisper.transcribe(loaded_model, audio=audio[from_index:to_index],
                                    verbose=True,
                                    language=current_language)

        if parts["text"] != "":
            parts["text"] += "\n\n"

        parts["text"] += result["text"]

        for segment in result["segments"]:
            segment["start"] += r[1]
            segment["end"] += r[1]
            for word in segment["words"]:
                word["start"] += r[1]
                word["end"] += r[1]
            parts["segments"].append(segment)

    out_file = out.rstrip("/") + "/" + os.path.basename(file)
    f = open(out_file + ".json", "w")
    f.write(json.dumps(parts))
    f.close()

    f = open(out_file + ".vtt", "w")
    f.write(to_web_vtt(parts["segments"]))
    f.close()

    f = open(out_file + ".srt", "w")
    f.write(to_srt(parts["segments"]))
    f.close()

    f = open(out_file + ".words.srt", "w")
    f.write(to_srt(parts["segments"], True))
    f.close()

    f = open(out_file + ".txt", "w")
    f.write(to_txt(parts["segments"]))
    f.close()


def convert_seconds_to_vtt_timestamp(seconds):
    # Convert seconds to a timedelta object
    delta = datetime.timedelta(seconds=seconds)

    # Create a datetime object with an arbitrary date
    arbitrary_date = datetime.datetime(1, 1, 1)

    # Add the timedelta to the arbitrary date
    result = arbitrary_date + delta

    # Format the resulting time as a string in the desired format
    timestamp = result.strftime("%H:%M:%S.%f")[:-3]  # Exclude the last 3 digits for milliseconds

    return timestamp


def convert_seconds_to_srt_timestamp(seconds):
    # Convert seconds to a timedelta object
    delta = datetime.timedelta(seconds=seconds)

    # Create a datetime object with an arbitrary date
    arbitrary_date = datetime.datetime(1, 1, 1)

    # Add the timedelta to the arbitrary date
    result = arbitrary_date + delta

    # Format the resulting time as a string in the desired format
    timestamp = result.strftime("%H:%M:%S,%f")[:-3]  # Exclude the last 3 digits for milliseconds

    return timestamp


def to_web_vtt(segments: []):
    text = "WEBVTT\n\n"

    for segment in segments:
        text += convert_seconds_to_vtt_timestamp(segment["start"])
        text += " --> "
        text += convert_seconds_to_vtt_timestamp(segment["end"])
        text += "\n"
        text += str(segment["text"]).strip()
        text += "\n\n"

    return text


def to_srt(segments: [], words: bool = False):
    text = ""

    for index, segment in enumerate(segments):
        if words:
            for word in segment["words"]:
                text += str(index + 1) + "\n"
                text += convert_seconds_to_srt_timestamp(word["start"])
                text += " --> "
                text += convert_seconds_to_srt_timestamp(word["end"])
                text += "\n"
                text += str(word["text"]).strip()
                text += "\n\n"
            continue

        text += str(index + 1) + "\n"
        text += convert_seconds_to_srt_timestamp(segment["start"])
        text += " --> "
        text += convert_seconds_to_srt_timestamp(segment["end"])
        text += "\n"
        text += str(segment["text"]).strip()
        text += "\n\n"

    return text


def to_txt(segments: []):
    text = ""

    for segment in segments:
        text += str(segment["text"]).strip() + "\n"

    return text


if __name__ == "__main__":
    main()
