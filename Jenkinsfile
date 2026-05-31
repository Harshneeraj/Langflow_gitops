pipeline {
    agent any

    environment {
        FLOWS_DIR = 'flows'
        REPO_URL  = 'https://raw.githubusercontent.com/Harshneeraj/langflow_gitops/main'
        HELM_PATH = './helm/langflow-runtime'
    }

    stages {
        stage('Detect Flow Changes') {
            steps {
                script {
                    def prevCommit = sh(
                        script: 'git rev-parse HEAD~1 2>/dev/null || git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    def currCommit = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    def changedFiles = sh(
                        script: "git diff --name-only ${prevCommit} ${currCommit}",
                        returnStdout: true
                    ).trim().split('\n')

                    def changedFlows = changedFiles.findAll {
                        it.startsWith("${FLOWS_DIR}/") && it.endsWith('.json')
                    }

                    if (changedFlows.isEmpty()) {
                        echo "No flow changes detected — nothing to deploy."
                        return
                    }

                    echo "Detected ${changedFlows.size()} changed flow(s): ${changedFlows.join(', ')}"

                    for (flowFile in changedFlows) {
                        def flowId      = flowFile.tokenize('/').last().replace('.json', '')
                        def fileUrl     = "${REPO_URL}/${flowFile}"
                        def releaseName = "langflow-${flowId}".toLowerCase()

                        echo "Deploying Helm release '${releaseName}' for flow '${flowId}'"
                        sh """
                            helm upgrade --install ${releaseName} ${HELM_PATH} \\
                              --set flow.flow-id=${flowId} \\
                              --set "flow.downloadFlows.flows[0].url=${fileUrl}"
                        """
                    }
                }
            }
        }
    }

    post {
        success { echo "All flows deployed successfully." }
        failure { echo "Deployment failed — check the logs above." }
    }
}
