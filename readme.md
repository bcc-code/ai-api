# Whisper API

This is a small golang wrapper that exposes a job queue for running [whisper](https://openai.com/blog/whisper/) jobs.

It currently queues up jobs and uses the `whisper` command line utility to run the jobs one at a time.

In addition it exposes some monitoring parameters so it can be supervised.

There is currently no support for uploading files so the files have to be locally available. Neither does it have any sort of 
keys or login as that is currently not needed in the environment.

## Known bugs/areas for improvement

* If it crashes or gets restarted the queue is lost
* `progress` is always 0. Could be improved by parsing the output and calculating approx how much of the file has been processed.
* Output is very "slow", as in the cmd caches a lot of output before it is dumped to stdout. If this could be tricked into dumping more often, then the progress would be made more obvious.
* 10 000 other things

