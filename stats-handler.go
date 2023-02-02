package main

import (
	"bufio"
	"fmt"
	"net/http"
	"os/exec"

	"github.com/gin-gonic/gin"
	"github.com/samber/lo"
)

type stats struct {
	Queued    int
	Running   int
	Processed int
}

func (h *handlers) Stats(c *gin.Context) {
	running := len(lo.Filter(h.processedJobs, func(j *Job, _ int) bool {
		return j.Status == JobStatusRunning
	}))
	c.JSON(http.StatusOK, stats{
		Queued:    len(h.queuedJobs),
		Running:   running,
		Processed: len(h.processedJobs) - running,
	})
}

func (h *handlers) Smi(c *gin.Context) {
	cmd := exec.Command("nvidia-smi")

	stdout, _ := cmd.StdoutPipe()
	cmd.Start()

	scanner := bufio.NewScanner(stdout)
	scanner.Split(bufio.ScanLines)
	out := ""
	for scanner.Scan() {
		m := scanner.Text()
		out += fmt.Sprintf("%s\n", m)
	}

	c.Data(http.StatusOK, "text/plain", []byte(out))
}
