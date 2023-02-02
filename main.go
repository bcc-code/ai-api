package main

import (
	"context"
	"os"

	"github.com/bcc-code/mediabank-bridge/log"
	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog"
)

func (h *handlers) manager(ctx context.Context) {
	for {
		if ctx.Err() != nil {
			return
		}

		if len(h.queuedJobs) > 0 {
			job := h.queuedJobs[0]
			h.queuedJobs = h.queuedJobs[1:]
			h.processedJobs = append(h.processedJobs, job)

			if len(h.processedJobs) > 10 {
				h.processedJobs = h.processedJobs[len(h.processedJobs)-10:]
			}
			runJob(job)
			continue
		}

		log.L.Info().Msg("Queue done. Waiting")

		select {
		case <-ctx.Done():
			return
		case <-h.queueChan:
			log.L.Info().Msg("New job")
			continue
		}
	}
}

func main() {
	log.ConfigureGlobalLogger(zerolog.DebugLevel)

	handler := NewHandlers()
	r := gin.Default()

	r.GET("/stats", handler.Stats)
	r.GET("/smi", handler.Smi)

	transcription := r.Group("/transcription/")
	transcription.POST("/job", handler.SubmitJob)
	transcription.GET("/jobs", handler.ListJobs)
	transcription.DELETE("/job/:id", handler.DeleteJob)
	transcription.GET("/job/:id", handler.GetJob)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8888"
	}

	managerContext, cancelManager := context.WithCancel(context.Background())
	go handler.manager(managerContext)

	r.Run(":" + port)
	cancelManager()
}
