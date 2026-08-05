# Kubernetes Observability Project – FastAPI App

## Overview

This project deploys a Python FastAPI application to Kubernetes and builds an end-to-end observability stack around it using Prometheus, Grafana, and Kubernetes metrics. The goal is to monitor workload health, resource usage, application latency, and error rates, and to validate that dashboards and alerts respond correctly during failure scenarios.

## Architecture

### FastAPI application

- Container image: `protocs2/fastapi-app:latest`
- Exposes:
  - `/health` for health checks
  - `/metrics` for Prometheus scraping
  - `/login/success`, `/login/fail`, `/items/process` for business metrics
  - `/slow` to simulate high latency
  - `/error` to simulate HTTP 500 errors

### Kubernetes deployment

- Namespace: `fastapi-app`
- Deployment: `fastapi-app` with 3 replicas
- Service: `fastapi-service` (`ClusterIP`, port 80 → target port 8000)

### Prometheus

- Scrapes the FastAPI `/metrics` endpoint via a `ServiceMonitor`.
- Collects Kubernetes metrics through kube-state-metrics and node exporters.

### Grafana

- Dashboards:
  - Cluster Overview
  - Workload & Deployment Health
  - Application Metrics
- Alerts:
  - Elevated error rate
  - Failed Deployment
  - High CPU
  - Memory Pressure
  - Pod Restarts

## FastAPI Metrics

The app is instrumented with Prometheus middleware and exposes:

- Counters:
  - `http_requests_total{method, path, status_code}`
  - `successful_logins_total`
  - `failed_logins_total`
  - `items_processed_total`
- Histogram:
  - `http_request_duration_seconds{method, path, status_code}` with buckets from 10 ms to 5 s
- Gauge:
  - `http_requests_in_flight`

## Dashboards

### Cluster Overview

Tracks overall Kubernetes cluster health, including:

- CPU utilization
- Memory utilization
- Resource requests and limits by namespace
- Pod and workload counts across the cluster

This dashboard is used to validate cluster-wide capacity and namespace-level resource consumption.

### Workload & Deployment Health

Tracks:

- Desired replicas vs available replicas for `fastapi-app`
- Per-pod CPU usage
- Per-pod memory usage (WSS)
- Container restarts over the last hour

This dashboard is used to verify that the deployment stays healthy during normal operation and rollouts.

### Application Metrics

Tracks:

- HTTP request rate
- Error rate
- Latency percentiles (p50/p95/p99)
- Business metrics such as successful vs failed logins and items processed over time

These panels are used to visualize error and latency tests.

## Alerts

Grafana alerting is configured for the main failure modes of the system:

- Elevated error rate — Fires when the application's HTTP error rate exceeds the alert threshold.
- Failed Deployment — Fires when the deployment fails to reach a healthy running state.
- High CPU — Fires when CPU usage stays above the alert threshold for too long.
- Memory Pressure — Fires when memory usage remains too high or the node/container is under pressure.
- Pod Restarts — Fires when pods restart repeatedly, indicating instability or crashes.

These alerts are configured to cover the main operational risks and complement the dashboards used in the tests below.

## Tests and Validation

**Pod Health Test**  
Delete one FastAPI pod in `fastapi-app` and verify that Kubernetes recreates it. Confirm that the deployment returns to 3 available replicas and that the workload dashboard reflects the change.

**Deployment Health Test**  
Trigger a deployment rollout for `fastapi-app` using `kubectl rollout restart` and verify that Kubernetes replaces the pods and completes successfully. Confirm that the workload dashboard shows pods cycling during the rollout and returns to 3 available replicas afterward.

**CPU Stress Test**  
Deploy a temporary CPU stress pod and observe node and pod CPU usage in Grafana.

**Memory Stress Test**  
Deploy a temporary memory stress pod and observe memory usage in Grafana.

**Error Rate Test**  
Port-forward the service and send requests to `/error` to generate HTTP 500 responses. Verify that request rate and error rate increase and that the alert fires if configured.

**Latency Test**  
Port-forward the service and send requests to `/slow` to generate delayed responses. Verify that p95/p99 latency rises and that the alert fires if configured.

## How to Run

```bash
docker build -t protocs2/fastapi-app:latest .
docker push protocs2/fastapi-app:latest

kubectl apply -f manifests/
kubectl rollout status deployment/fastapi-app -n fastapi-app
kubectl get pods -n fastapi-app

kubectl port-forward -n fastapi-app svc/fastapi-service 8000:80
```

Then test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:8000/slow
curl -i http://localhost:8000/error
```