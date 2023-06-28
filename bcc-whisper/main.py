import whisper, torch, ssl, math, json, os
from song_or_not.classifier import AudioClassifier
from song_or_not.inference import inference

ssl._create_default_https_context = ssl._create_unverified_context

SAMPLE_RATE = 16000
LENGTH = 5  # seconds
SAMPLES_PER_CHUNK = SAMPLE_RATE * LENGTH

def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = torch.load("song_or_not/songornot_5s.pt", map_location=torch.device(device))
    model.eval()

    os.makedirs("out", exist_ok=True)

    files = os.listdir("files")

    for file in files:
        if file.endswith(".wav"):
            transcribeFile(model, device, "files/" + file)

def transcribeFile(model, device: torch.device, file: str):
    res = inference(model, file, device, SAMPLE_RATE, SAMPLES_PER_CHUNK, LENGTH)
    res2 = []

    current_type = "song"
    start = 0
    end = 0

    res2: list[tuple[str, int, int]]= []

    for x in res:
        d = x[1]
        # The sensitivity can be adjusted here a bit
        if d <= 2 or current_type == x[0]:
            end += d
        else:
            print(x)
            if current_type == "speech":
                res2.append((current_type, start*LENGTH, end*LENGTH))
            start = end
            end = end + x[1]
            current_type = x[0]

    if current_type == "speech":
        res2.append((current_type, start*LENGTH, end*LENGTH))

    print(res2)

    audio = whisper.load_audio(file, SAMPLE_RATE)

    parts = []

    for r in res2:
        fromIndex = math.floor(r[1]*SAMPLE_RATE)
        toIndex = math.floor(r[2]*SAMPLE_RATE)

        result = whisper.load_model("medium").transcribe(audio=audio[fromIndex:toIndex], language="no", verbose=True)

        lines = []
        for segment in result["segments"]:
            lines.append({
                "start": segment["start"], # type: ignore
                "end": segment["end"], # type: ignore
                "text": segment["text"] # type: ignore
            })
        
        parts.append({
            "start": r[1],
            "end": r[2],
            "transcription": lines,
        })

    f = open("out/" + str.split(file, "/").pop() + ".json", "w")
    f.write(json.dumps(parts))
    f.close()

if __name__ == "__main__":
    main()
