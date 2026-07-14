# Shopping App

A cloud-native shopping list application built with FastAPI, PostgreSQL and a static frontend.

The application is containerized with Docker and deployed to Kubernetes through a GitOps workflow using GitHub Actions, Helm and Argo CD.

## Features

- FastAPI REST API
- HTML, CSS and JavaScript frontend
- PostgreSQL persistence
- Create, list and delete shopping items
- Health-check endpoint
- OpenAPI and Swagger documentation
- Docker container image
- Automated CI/CD pipeline with GitHub Actions

## Application architecture

```text
Browser
   |
   | HTTPS
   v
NGINX Ingress
   |
   v
Shopping App Service
   |
   v
FastAPI Pods
   |
   v
PostgreSQL Service
   |
   v
PostgreSQL Pod
