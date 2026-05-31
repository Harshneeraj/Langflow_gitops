FROM jenkins/jenkins:lts

USER root

# Install Docker CLI, kubectl, and Helm
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      docker.io curl apt-transport-https ca-certificates gnupg lsb-release sudo && \
    rm -rf /var/lib/apt/lists/*

# kubectl
RUN curl -fsSL -o /usr/local/bin/kubectl \
      https://dl.k8s.io/release/v1.33.2/bin/linux/amd64/kubectl && \
    chmod +x /usr/local/bin/kubectl

# Helm
RUN curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# Allow Jenkins to use Docker
RUN usermod -aG docker jenkins

USER jenkins
