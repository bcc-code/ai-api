import whisper
from song_or_not import AudioClassifier
import song_or_not
import torch
import sys

SAMPLE_RATE = 44100
LENGTH = 5  # seconds
SAMPLES_PER_CHUNK = SAMPLE_RATE * LENGTH
FILE = "/Users/matjaz/meeting.wav"


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = torch.load("song_or_not/songornot_5s.pt", map_location=torch.device(device))
    model.eval()
    res = song_or_not.inference2(model, FILE, device, SAMPLE_RATE, SAMPLES_PER_CHUNK)
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

    audio = whisper.audio.load_audio("/Users/matjaz/meeting.wav", SAMPLE_RATE)
    t = whisper.load_model("medium").transcribe(audio=audio[15*60*SAMPLE_RATE:17*60*SAMPLE_RATE], language="no", verbose=True)
    print(t)


if __name__ == "__main__":
    main()
