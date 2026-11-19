pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE_NAME = 'sachin2991/simple-web-app'
        DOCKER_CREDENTIALS = 'dockerhub-creds'
        GITHUB_CREDENTIALS = 'github-creds'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Detect Application Changes') {
            steps {
                script {
                    def appFiles = [
                        'simple-web-app/app.py',
                        'simple-web-app/Dockerfile',
                        'simple-web-app/requirements.txt',
                        'simple-web-app/tests/test_app.py'
                    ]

                    def appChanged = false

                    for (changeSet in currentBuild.changeSets) {
                        for (entry in changeSet.items) {
                            for (file in entry.affectedFiles) {
                                if (appFiles.contains(file.path)) {
                                    appChanged = true
                                }
                            }
                        }
                    }

                    // Build on the first run, even without a changelog.
                    if (currentBuild.previousBuild == null) {
                        appChanged = true
                    }

                    env.BUILD_APP = appChanged.toString()

                    echo "Application source changed: ${env.BUILD_APP}"
                }
            }
        }

        stage('Python Validation') {
            when {
                expression { env.BUILD_APP == 'true' }
            }
            steps {
                sh '''
                    python3 -m py_compile simple-web-app/app.py
                    echo "Python syntax validation successful"
                '''
            }
        }
        stage('Automated Tests') {
    when {
        expression { env.BUILD_APP == 'true' }
    }
    steps {
        sh '''
            if [ ! -x "$WORKSPACE/.venv-ci/bin/python" ]; then
                python3 -m venv "$WORKSPACE/.venv-ci"
            fi

            "$WORKSPACE/.venv-ci/bin/pip" install \
                -r simple-web-app/requirements.txt pytest

            cd simple-web-app

            ../.venv-ci/bin/python -m pytest tests/ -v
        '''
    }
}
        stage('Build Docker Image') {
            when {
                expression { env.BUILD_APP == 'true' }
            }
            steps {
                sh '''
                    docker build \
                      -t ${IMAGE_NAME}:${IMAGE_TAG} \
                      -t ${IMAGE_NAME}:latest \
                      simple-web-app
                '''
            }
        }

        stage('Push to Docker Hub') {
            when {
                expression { env.BUILD_APP == 'true' }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_TOKEN'
                    )
                ]) {
                    sh '''
                        echo "$DOCKER_TOKEN" | docker login \
                            -u "$DOCKER_USER" --password-stdin

                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:latest

                        docker logout
                    '''
                }
            }
        }

        stage('Update Kubernetes Manifest') {
            when {
                expression { env.BUILD_APP == 'true' }
            }
            steps {
                sh '''
                    sed -i "s|image: .*|image: ${IMAGE_NAME}:${IMAGE_TAG}|" \
                        simple-web-app/deployments.yaml

                    git config user.name "Jenkins CI"
                    git config user.email "jenkins@localhost"

                    git add simple-web-app/deployments.yaml

                    git diff --cached --quiet || \
                        git commit -m "Update application image to ${IMAGE_TAG}"
                '''
            }
        }

        stage('Push Manifest to GitHub') {
            when {
                expression { env.BUILD_APP == 'true' }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: "${GITHUB_CREDENTIALS}",
                        usernameVariable: 'GITHUB_USER',
                        passwordVariable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        ASKPASS_FILE="$(mktemp)"
                        trap 'rm -f "$ASKPASS_FILE"' EXIT

                        cat > "$ASKPASS_FILE" <<'EOF'
#!/bin/sh
case "$1" in
    *Username*) printf '%s\\n' "$GITHUB_USER" ;;
    *Password*) printf '%s\\n' "$GITHUB_TOKEN" ;;
esac
EOF

                        chmod 700 "$ASKPASS_FILE"

                        export GIT_ASKPASS="$ASKPASS_FILE"
                        export GIT_TERMINAL_PROMPT=0

                        git push https://github.com/sachin-prog/kubernetes_projects.git HEAD:main
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'CI pipeline completed successfully!'
            echo 'Argo CD will synchronize the updated Kubernetes manifest.'
        }

        failure {
            echo 'CI/CD pipeline failed. Check the Jenkins console output.'
        }
    }
}
