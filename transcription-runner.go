package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net/http"
	"os/exec"
	"strings"
	"time"

	"github.com/bcc-code/mediabank-bridge/log"
)

func runJob(job *Job) {
	log.L.Info().Str("path", job.Path).Msg("Processing started")
	job.Status = JobStatusRunning

	cmd := exec.Command("whisper",
		"--task", "transcribe",
		"--model", "large-v2",
		"--output_format", job.OutputFormat,
		"--output_dir", job.OutputPath,
		"--language", job.Language,
		job.Path,
	)
	//cmd := exec.Command("/bin/bash", "-c", "sleep 30")

	stderr, _ := cmd.StderrPipe()
	stdout, _ := cmd.StdoutPipe()

	start := time.Now()
	cmd.Start()

	go func() {
		scanner := bufio.NewScanner(stderr)
		scanner.Split(bufio.ScanWords)
		for scanner.Scan() {
			m := scanner.Text()
			fmt.Println(m)
		}
	}()

	scanner := bufio.NewScanner(stdout)
	scanner.Split(bufio.ScanLines)
	for scanner.Scan() {
		m := scanner.Text()
		job.Result += fmt.Sprintf("%s\n", m)
		fmt.Println(m)
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

	if job.Callback != "" {
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
