# Langflow CI/CD

Automated deployment of [Langflow](https://github.com/langflow-ai/langflow) flows on Kubernetes using Jenkins and Helm.

![Architecture](AI_Kitchen_Umbrella.drawio.png)

## What this does

Every time you push a flow JSON file to the `flows/` directory, Jenkins detects the change and deploys that flow as its own isolated Kubernetes workload — no manual `helm install` needed.

The full stack includes:

| Component | Purpose |
|-----------|---------|
| **Langflow** | Visual AI flow builder and runtime |
| **LiteLLM** | Unified LLM proxy (OpenAI, Groq, Anthropic, etc.) |
| **PostgreSQL** | Persistent storage for Langflow and LiteLLM |
| **Jenkins** | CI/CD orchestrator, triggered by GitHub webhooks |

## Repository layout

```
Langflow_CICD/
├── flows/                      # Langflow flow JSON files (one per flow)
│   └── rag3.json               # Example: RAG flow using AstraDB
│
├── helm/
│   ├── kitchen-umbrella/       # Full-stack chart (Langflow + LiteLLM + Postgres)
│   └── langflow-runtime/       # Per-flow runtime chart (deployed once per flow)
│
├── jenkins/
│   └── Dockerfile              # Jenkins image with Docker, kubectl, and Helm pre-installed
│
├── launcher/
│   ├── Pod_Launcher.py         # FastAPI service that dynamically creates Langflow deployments
│   ├── Dockerfile              # Container image for the launcher service
│   └── engine-rbac.yaml        # Kubernetes RBAC for the launcher's service account
│
├── components/
│   └── ChatLiteLLM.py          # Custom Langflow component for LiteLLM integration
│
├── Jenkinsfile                 # Pipeline definition
└── AI_Kitchen_Umbrella.drawio  # Architecture diagram source
```

## How it works

### 1. Developer pushes a flow

```
git add flows/my-new-flow.json
git commit -m "add my-new-flow"
git push
```

### 2. Jenkins detects the change

The Jenkinsfile compares the current commit to the previous one, finds any new or modified `.json` files under `flows/`, and deploys each one.

### 3. Helm deploys the flow

Each flow gets its own Helm release using the `langflow-runtime` chart:

```
helm upgrade --install langflow-my-new-flow ./helm/langflow-runtime \
  --set flow.flow-id=my-new-flow \
  --set downloadFlows.flows[0].url=https://raw.githubusercontent.com/.../flows/my-new-flow.json
```

The runtime pod downloads the flow JSON at startup and runs Langflow in backend-only mode.

### 4. Environments

| Namespace | What runs there |
|-----------|----------------|
| `dev` | Langflow dev instance (full UI + backend) |
| `prod` | One Helm release per production flow |
| `litellm` | LiteLLM proxy server |

## Quick start

### Prerequisites

- Kubernetes cluster (local: kind, k3s, or minikube)
- Helm 3
- Jenkins with the GitHub plugin and ngrok (for webhook delivery)

### 1. Deploy the full stack

```bash
helm upgrade --install kitchen ./helm/kitchen-umbrella \
  --set postgresql.auth.password=yourpassword
```

This deploys Langflow, LiteLLM, and Postgres in one release.

### 2. Set up Jenkins

Build and run the Jenkins image:

```bash
docker build -t jenkins-langflow ./jenkins
docker run -d \
  --name jenkins-langflow \
  --network=host \
  -e KUBECONFIG=/home/jenkins/.kube/config \
  -v ~/.kube:/home/jenkins/.kube \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home:/var/jenkins_home \
  jenkins-langflow
```

Configure a GitHub webhook pointing at your Jenkins instance (use ngrok if running locally).

### 3. Deploy a flow manually

```bash
helm upgrade --install langflow-rag3 ./helm/langflow-runtime \
  --set flow.flow-id=rag3 \
  --set "flow.downloadFlows.flows[0].url=https://raw.githubusercontent.com/Harshneeraj/Langflow_CICD/main/flows/rag3.json"
```

### 4. (Optional) Run the Pod Launcher

The launcher is a FastAPI service that lets you spin up new Langflow deployments via HTTP:

```bash
# Deploy the launcher
kubectl apply -f launcher/engine-rbac.yaml
kubectl run launcher --image=your-registry/launcher:latest --port=8000

# Create a new Langflow deployment
curl -X POST http://localhost:8000/launch-langflow/
```

## Helm chart reference

### kitchen-umbrella

Deploys the full stack in one release. Key values:

```yaml
postgresql:
  auth:
    username: shareduser
    password: sharedpass
    database: shareddb,langflow

langflow:
  image:
    repository: langflowai/langflow
    tag: latest
  backend:
    externalDatabase:
      host: kitchen-umbrella-postgres
      port: "5432"
      user: shareduser
      password: sharedpass
      database: langflow

litellm:
  db:
    host: kitchen-umbrella-postgres
    database: shareddb
```

### langflow-runtime

Deploys a single flow. Key values:

```yaml
flow:
  flow-id: your-flow-id
  image:
    repository: langflowai/langflow
    tag: latest
  downloadFlows:
    path: /app/flows
    flows:
      - url: https://raw.githubusercontent.com/.../flows/your-flow.json
  backend:
    externalDatabase:
      host: kitchen-umbrella-postgres
      database: langflow_prd
```

## Included flows

| File | Description |
|------|-------------|
| `flows/rag3.json` | RAG pipeline: File → Split → AstraDB (ingest) + AstraDB (search) → OpenAI → Chat |

## Custom components

### `components/ChatLiteLLM.py`

A Langflow component that connects to a LiteLLM proxy instead of calling LLM providers directly. Drop it into your Langflow components directory to use it in flows.

Configuration:
- **API Base URL** — your LiteLLM proxy address (e.g. `http://litellm-service:4000`)
- **API Key** — the LiteLLM master key
- **Model** — dynamically fetched from the proxy's `/models` endpoint

## Architecture

```
GitHub (push)
    │
    │ webhook
    ▼
Jenkins
    │
    │ helm upgrade --install
    ▼
Kubernetes cluster
    ├── dev namespace
    │   └── Langflow (dev)  ──── Langflow Dev DB (RDS)
    │
    ├── prod namespace
    │   ├── langflow-flow-1  ──┐
    │   └── langflow-flow-2  ──┴── Langflow Prod DB (RDS)
    │
    └── litellm namespace
        └── LiteLLM proxy  ──── LiteLLM DB (RDS)
```

Each production flow is an independent Helm release. Adding a new flow = pushing a JSON file.
