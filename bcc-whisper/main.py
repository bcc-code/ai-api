import whisper
from song_or_not.classifier import AudioClassifier
from song_or_not.inference import inference
import torch
import sys
import ssl
import math

ssl._create_default_https_context = ssl._create_unverified_context

SAMPLE_RATE = 16000
LENGTH = 5  # seconds
SAMPLES_PER_CHUNK = SAMPLE_RATE * LENGTH
FILE = "/Users/fredrikvedvik/Desktop/fkaare.wav"


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = torch.load("song_or_not/songornot_5s.pt", map_location=torch.device(device))
    model.eval()
    res = inference(model, FILE, device, SAMPLE_RATE, SAMPLES_PER_CHUNK, LENGTH)
    res2 = []

    current_type = "song"
    start = 0
    end = 0

    res2 = []

    for x in res:
        d = x[1]
        # The sensitivity can be adjusted here a bit
        if d <= 2 or current_type == x[0]:
            end += d
        else:
            if current_type == "speech":
                res2.append((current_type, start*LENGTH, end*LENGTH))
            start = end
            end = end + x[1]
            current_type = x[0]

    if current_type == "speech":
        res2.append((current_type, start*LENGTH, end*LENGTH))

    print(res2)

    audio = whisper.load_audio(FILE, SAMPLE_RATE)

    fromIndex = math.floor(0.33*60*SAMPLE_RATE)
    toIndex = math.floor(3*60*SAMPLE_RATE)

    t = whisper.load_model("medium").transcribe(audio=audio[fromIndex:toIndex], language="no", verbose=True)
    print(t)


if __name__ == "__main__":
    main()
