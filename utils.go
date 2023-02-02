package main

import (
	"net/http"
	"time"
)

func remove[T any](slice []T, s int) []T {
	return append(slice[:s], slice[s+1:]...)
}

var httpClient = http.Client{
	Timeout: 2 * time.Second,
}
