import argparse
import copy
import json
import math
import ssl
from datasets import Dataset, Audio
#import whisper_timestamped as whisper
import whisper
import os
import datetime
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from inference import load_model, inference, AudioClassifier

# noinspection PyProtectedMember
ssl._create_default_https_context = ssl._create_unverified_context

SAMPLE_RATE = 16000
LENGTH = 5  # seconds
SAMPLES_PER_CHUNK = SAMPLE_RATE * LENGTH


def parse_arguments():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--language", help="language", default="no")
    parser.add_argument("-m", "--model", help="whisper model to use", default="openai/whisper-large-v3")
    parser.add_argument("src", help="source file")
    parser.add_argument("output", help="output file")

    return parser.parse_args()


def main():
    # import for side effects
    _ = AudioClassifier

    config = vars(parse_arguments())
    file = config["src"]
    out = config["output"]
    language = config["language"]

    model = config["model"]

    transcribe_file(file, out, language, model)

def transcribe_file(file: str, out: str, language: str, model_id: str):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    detection_model = load_model(device)
    detection_model.eval()
    classified_segments = inference(detection_model, file, device, SAMPLE_RATE, SAMPLES_PER_CHUNK, LENGTH)

    current_type = "song"

    # start and end are in chunks / segments. So timestamp is start * LENGTH and end * LENGTH
    start = 0
    end = 0

    speech_segments: list[tuple[str, int, int]] = []

    # Filter out non-speech and join continuous speech segments
    for x in classified_segments:
        d = x[1]
        # The sensitivity can be adjusted here a bit
        if d <= 3 or current_type == x[0]:
            end += d
        else:
            print(x)
            if current_type == "speech":
                speech_segments.append((current_type, start * LENGTH, end * LENGTH))
            start = end
            end = end + x[1]
            current_type = x[0]

    if current_type == "speech":
        speech_segments.append((current_type, start * LENGTH, end * LENGTH))

    print(res2)

    ## This works but currently don't know what to do with it, so it is disabled
    #p = Pipeline.from_pretrained( "pyannote/speaker-diarization-3.1", use_auth_token="<REPLACE WITH TOKEN>")
    #diarization = p(file)
    #print(diarization)

    # Load aduio file and just fetch the audio part of it
    audio = Dataset.from_dict( {"audio": [file]}).cast_column("audio", Audio())[0]["audio"]

    # Load model and set up the pipeline
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )

    parts = {
        "text": "",
        "segments": [],
        "language": language,
    }

    # Transcribe each speech segment
    for r in speech_segments:
        from_index = math.floor(r[1] * audio["sampling_rate"])
        to_index = math.floor(r[2] * audio["sampling_rate"])

        # No kwargs is automatic language detection
        kwargs = None
        if language != "" and language != "auto":
            kwargs = {"language": language}

        # If we do not copy it then in the next loop the ["array"] no longer exists for some dumb reason
        a2 = copy.deepcopy(audio)

        # Cut the chunk we want to transcribe out of the audio
        a2["array"] = audio["array"][from_index:to_index]

        # do the trnscription
        result = pipe(a2, return_timestamps="word", return_language=True, generate_kwargs=kwargs)


        # Adjust timestamps and forrmat of the data
        if parts["text"] != "":
            parts["text"] += "\n\n"

        parts["text"] += result["text"]

        segment = None
        word_count = 0
        for rchunk in result["chunks"]:
            if segment is None:
                segment = {
                    "text": "",
                    "start": rchunk["timestamp"][0] + r[1],
                    "words": [],
                }

            rchunk["text"] = rchunk["text"].strip()
            segment["end"] = rchunk["timestamp"][1] + r[1]
            segment["text"] += " " + rchunk["text"]

            segment["words"].append({
                "text": rchunk["text"],
                "start": rchunk["timestamp"][0] + r[1],
                "end": rchunk["timestamp"][1] + r[1],
            })

            word_count+=1

            # This controls what we consider one line in the srt file
            if word_count > 11 or (word_count > 5 and rchunk['text'][-1] in "!?.:"):
                parts["segments"].append(segment)
                print(segment["text"])
                segment = None
                word_count = 0

            # In the first round the language is not set... Yeah, I don't know what the deal is either
            if (parts["language"] == "" or parts["language"] == "auto") and result["chunks"][0]['language'] is not None:
                parts["language"] = result["chunks"][0]['language']

        if segment is not None:
            parts["segments"].append(segment)

    print(parts)

    # Write the results to files in various formats
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

