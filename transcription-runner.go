package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/bcc-code/mediabank-bridge/log"
)

func doCallback(job *Job) {
	if job.Callback != "" {
		log.L.Info().Str("callback", job.Callback).Msg("Doing callback")
		jobJson, err := json.Marshal(job)
		if err != nil {
			log.L.Error().Err(err).Msg("Failed to execute callback")
		}

		r, err := http.NewRequest("POST", job.Callback, strings.NewReader(string(jobJson)))
		if err != nil {
			log.L.Error().Err(err).Msg("Failed to execute callback")
		}

		_, err = httpClient.Do(r)
		if err != nil {
			log.L.Error().Err(err).Msg("Failed to execute callback")
		}
	}
}

func runJob(job *Job) {
	log.L.Info().Str("path", job.Path).Msg("Processing started")
	job.Status = JobStatusRunning

	if os.Getenv("DO_NOT_ACTUALLY_RUN_COMMAND") == "true" {
		log.L.Warn().Msg("FAKE RUNNING COMMAND")
		// Simulate some work
		time.Sleep(time.Second * 10)
		job.Duration = fmt.Sprintf("duration: %s", time.Second*10)
		job.Status = JobStatusCompleted
		doCallback(job)
		return
	}

	//cmd := exec.Command("whisper",
	//	"--task", "transcribe",
	//	"--model", "large-v2",
	//	"--output_format", job.OutputFormat,
	//	"--output_dir", job.OutputPath,
	//	"--language", job.Language,
	//	job.Path,
	//)

	cmd := exec.Command("python3", "bcc-whisper/main.py", "-o", job.OutputPath, "-l", job.Language, job.Path)

	cmd.Env = append(os.Environ(), "PYTHONUNBUFFERED=1")

	stderr, _ := cmd.StderrPipe()
	stdout, _ := cmd.StdoutPipe()

	start := time.Now()
	_ = cmd.Start()

	go func() {
		scanner := bufio.NewScanner(stderr)
		scanner.Split(bufio.ScanLines)
		for scanner.Scan() {
			fmt.Print(scanner.Text())
		}
	}()

	scanner := bufio.NewScanner(stdout)
	scanner.Split(bufio.ScanLines)
	for scanner.Scan() {
		fmt.Println(scanner.Text())
	}

	err := cmd.Wait()
	end := time.Now()

	duration := end.Sub(start)
	job.Duration = fmt.Sprintf("duration: %s", duration)
	log.L.Info().
		Str("duration", job.Duration).
		Int("exit code", cmd.ProcessState.ExitCode()).
		Err(err).
		Msg("Finished")

	if cmd.ProcessState.ExitCode() != 0 {
		job.Status = JobStatusFailed
		return
	}

	job.Status = JobStatusCompleted
	log.L.Info().Str("path", job.Path).Msg("Processing completed")
	doCallback(job)
}
