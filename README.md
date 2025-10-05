# Langflow_CICD
Create a CICD pipeline for Langflow

![Langflow CICD Architecture](https://github.com/Harshneeraj/Langflow_CICD/blob/main/AI_Kitchen_Umbrella.drawio.png)

📘 Architecture Documentation
Overview

This architecture automates the deployment and management of Langflow flows and a LiteLLM Proxy Server in Kubernetes using Helm charts and Jenkins CI/CD pipelines. It ensures isolated environments for development and production, and integrates with Amazon RDS for persistent data storage.

Components
1. Source Control (GitHub)

Developers commit code and flow definitions to GitHub.

GitHub integrates with Jenkins to trigger builds automatically after each commit (via webhooks).

2. Jenkins

Acts as the CI/CD orchestrator.

Integrated with ngrok for secure external webhook triggering.

On code commit:

Jenkins triggers the Langflow-Runtime Helm chart build and deployment.

Builds are parameterized to handle both dev and prod namespaces.

3. Helm

Helm is used for packaging and deploying Kubernetes applications.

Two types of Helm charts are used:

Kitchen-Umbrella Chart: A parent chart responsible for deploying multiple sub-components in one release.

Langflow-Runtime Chart: Defines the runtime environment for Langflow flows. Each flow is released as a separate Helm release.

4. Namespaces

Namespaces isolate environments within the Kubernetes cluster:

a. Dev Namespace

Runs Langflow Dev.

Intended for development and testing of flows.

Uses a dedicated database (Langflow Dev DB) in Amazon RDS.

b. Prod Namespace

Runs multiple production-ready flows:

Langflow Prod Flow-1

Langflow Prod Flow-2

Each flow is deployed independently via separate Helm releases.

Provides isolation and scalability for production workloads.

c. LiteLLM Namespace

Hosts the LiteLLM Proxy Server, which provides LLM inference services for Langflow.

Connects to LiteLLM DB in Amazon RDS for persistent state management.

5. Databases (Amazon RDS)

Langflow Dev DB → Stores data related to the development instance of Langflow.

LiteLLM DB → Stores data for the LiteLLM Proxy Server.

Amazon RDS ensures persistence, reliability, and backup support for both databases.

Deployment Flow

Code Commit

A developer pushes changes to GitHub.

Build Trigger

Jenkins, integrated with ngrok, receives the webhook and triggers a build.

Helm Deployment

Jenkins applies the Langflow-Runtime Chart.

Each flow gets its own Helm release (isolation per flow).

Environment Segregation

Dev flows are deployed into the Dev Namespace.

Production flows are deployed into the Prod Namespace.

LiteLLM Integration

LiteLLM Proxy Server is deployed into its dedicated namespace.

It integrates with Langflow (both Dev and Prod) to handle LLM requests.

Data Persistence

Langflow and LiteLLM communicate with Amazon RDS for storage.

Separate databases ensure isolation of dev and prod data.

Key Features

Environment Isolation: Dev and Prod workloads are separated at the namespace and DB level.

Helm-based Deployment: Easy to upgrade, rollback, and maintain multiple flows.

Scalability: Multiple Langflow flows can run in production, each as an independent release.

CI/CD Integration: Automated deployments triggered by GitHub commits via Jenkins.

Persistence & Reliability: Amazon RDS provides durable storage for Langflow and LiteLLM.
