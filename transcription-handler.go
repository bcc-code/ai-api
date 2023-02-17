package main

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/samber/lo"
)

type Job struct {
	ID           string `json:"id"`
	Path         string `json:"path"`
	Language     string `json:"language"`
	OutputFormat string `json:"format"`
	OutputPath   string `json:"output_path"`
	Progress     int    `json:"progress"`
	Status       string `json:"status"`
	Result       string `json:"result"`
	Callback     string `json:"callback"`
	Model        string `json:"model"`
	Duration     string `json:"duration"`
	Priority     int    `json:"priority"`
}

type handlers struct {
	queuedJobs    []*Job
	processedJobs []*Job
	queueChan     chan bool
}

func NewHandlers() *handlers {
	return &handlers{
		queuedJobs:    []*Job{},
		processedJobs: []*Job{},
		queueChan:     make(chan bool, 2),
	}
}

const (
	JobStatusQueued    = "QUEUED"
	JobStatusRunning   = "RUNNING"
	JobStatusCompleted = "COMPLETED"
	JobStatusFailed    = "FAILED"
)

func (h *handlers) SubmitJob(c *gin.Context) {
	job := &Job{}
	err := c.BindJSON(job)
	if err != nil {
		c.AbortWithError(http.StatusBadRequest, err)
		return
	}

	job.ID = uuid.New().String()
	job.Status = JobStatusQueued

	if job.Priority <= 0 {
		// This is the default value. We want the default to be 1000 now so the jobs get appended to the front of the queue.
		job.Priority = 1000
	}

	if job.OutputFormat == "" {
		job.OutputPath = "txt"
	}

	if job.Model == "" {
		job.Model = "large-v2"
	}

	if job.Priority >= 500 {
		// High prio. Put in the front
		h.queuedJobs = append([]*Job{job}, h.queuedJobs...)
	} else {
		// Low prio, put in the back
		h.queuedJobs = append(h.queuedJobs, job)
	}

	// Attempt to send. If buffer is full, ignore
	select {
	case h.queueChan <- true:
	case <-time.After(50 * time.Millisecond):
	}

	c.JSON(http.StatusAccepted, job)
}

func (h *handlers) ListJobs(c *gin.Context) {
	c.JSON(http.StatusOK, append(h.queuedJobs, h.processedJobs...))
}

func (h *handlers) DeleteJob(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		c.AbortWithStatus(http.StatusNotFound)
		return
	}

	if _, index, ok := lo.FindIndexOf(h.queuedJobs, func(i *Job) bool { return i.ID == id }); ok {
		h.queuedJobs = remove(h.queuedJobs, index)
	}

	c.Status(http.StatusNoContent)
}

func (h *handlers) GetJob(c *gin.Context) {
	id := c.Param("id")
	jobs := append(h.queuedJobs, h.processedJobs...)
	if _, index, ok := lo.FindIndexOf(jobs, func(i *Job) bool { return i.ID == id }); ok {
		c.JSON(http.StatusOK, jobs[index])
		return
	}

	c.Status(http.StatusNotFound)
}
