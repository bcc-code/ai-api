run:
	go run .

build:
	rm -fr ./build
	go build -o build/bin .
	mkdir ./build/bcc-whisper
	cp ./bcc-whisper/*.py ./build/bcc-whisper/
	cp ./bcc-whisper/*.txt ./build/bcc-whisper/

build-linux-amd64:
	rm -fr ./build
	GOOS=linux GOARCH=amd64 go build -o build/bin .
	mkdir ./build/bcc-whisper
	cp ./bcc-whisper/*.py ./build/bcc-whisper/
	cp ./bcc-whisper/*.txt ./build/bcc-whisper/
