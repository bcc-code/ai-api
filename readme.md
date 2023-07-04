# Whisper API

This is a small golang wrapper that exposes a job queue for running [whisper](https://openai.com/blog/whisper/) jobs.

It currently queues up jobs and uses the `whisper` command line utility to run the jobs one at a time.

In addition it exposes some monitoring parameters so it can be supervised.

There is currently no support for uploading files so the files have to be locally available. Neither does it have any sort of 
keys or login as that is currently not needed in the environment.

## Building

You will need at least Go 1.19, can be obtained from https://go.dev/
Then run `make build` to build for your architecture or `make build-linux-amd64` to build for linux/amd64 combo.

This will produce a `whisper-api` in the current directory.

## Known bugs/areas for improvement

* If it crashes or gets restarted the queue is lost
* `progress` is always 0. Could be improved by parsing the output and calculating approx how much of the file has been processed.
* Output is very "slow", as in the cmd caches a lot of output before it is dumped to stdout. If this could be tricked into dumping more often, then the progress would be made more obvious.
* 10 000 other things

## Deployment

Build the directory for deployment on linux with `make build-linux-amd64` and copy the resulting directory to the server. At the moment this is deployed on `ai-api:/api/` (executable at `/api/bin`)