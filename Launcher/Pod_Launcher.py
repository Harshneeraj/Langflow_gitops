"""Pod Launcher — a FastAPI service that dynamically creates Langflow deployments.

POST /launch-langflow/
    Creates a new Kubernetes Deployment running Langflow in backend-only mode.
    Returns the deployment name so the caller can track it.

Requirements:
    pip install fastapi uvicorn kubernetes

The service account running this pod needs the RBAC permissions defined
in engine-rbac.yaml.
"""
from fastapi import FastAPI, HTTPException
from kubernetes import client, config
import uuid

app = FastAPI(title="Langflow Pod Launcher", version="1.0.0")

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

apps_v1 = client.AppsV1Api()


@app.post("/launch-langflow/", summary="Create a new Langflow deployment")
async def launch_langflow():
    deployment_name = f"langflow-{uuid.uuid4().hex[:8]}"

    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(
            name=deployment_name,
            labels={"app": "langflow", "managed-by": "pod-launcher"},
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": deployment_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="langflow",
                            image="langflowai/langflow:latest",
                            image_pull_policy="IfNotPresent",
                            ports=[client.V1ContainerPort(container_port=7860)],
                            env=[
                                client.V1EnvVar(name="LANGFLOW_BACKEND_ONLY",            value="true"),
                                client.V1EnvVar(name="LANGFLOW_LOAD_FLOWS_PATH",         value="/app/flows"),
                                client.V1EnvVar(name="LANGFLOW_SUPERUSER",               value="administrator"),
                                client.V1EnvVar(name="LANGFLOW_SUPERUSER_PASSWORD",      value="securepassword"),
                                client.V1EnvVar(name="LANGFLOW_CONFIG_DIR",              value="/app/langflow"),
                                client.V1EnvVar(name="LANGFLOW_COMPONENTS_PATH",         value="/app/langflow/components"),
                                client.V1EnvVar(name="LANGFLOW_SAVE_DB_IN_CONFIG_DIR",   value="false"),
                                client.V1EnvVar(name="LANGFLOW_UPDATE_STARTER_PROJECTS", value="true"),
                                client.V1EnvVar(
                                    name="LANGFLOW_DATABASE_URL",
                                    value="postgresql://admin:admin@postgres:5432/langflow-prod",
                                ),
                            ],
                            resources=client.V1ResourceRequirements(
                                requests={"memory": "256Mi", "cpu": "250m"},
                                limits={"memory": "1Gi", "cpu": "500m"},
                            ),
                        )
                    ]
                ),
            ),
        ),
    )

    try:
        apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    except client.ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes error: {e.reason}") from e

    return {"status": "created", "deployment_name": deployment_name}


@app.get("/health")
async def health():
    return {"status": "ok"}
