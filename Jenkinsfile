pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/your-repo/sentinelflux-framework.git'
            }
        }

        stage('Setup Environment') {
            steps {
                sh 'python3 -m venv venv'
                sh 'venv/bin/pip install -r requirements.txt'
                sh 'venv/bin/playwright install'
            }
        }

        stage('Run API Tests') {
            steps {
                sh 'venv/bin/pytest tests/api/ -v --junitxml=reports/api-results.xml'
            }
        }

        stage('Run Web UI Tests') {
            steps {
                sh 'venv/bin/pytest tests/web/ --browser chromium --headed=false -v --junitxml=reports/web-results.xml'
            }
        }

        stage('Run GraphQL Tests') {
            steps {
                sh 'venv/bin/pytest tests/api/test_graphql_api.py -v --junitxml=reports/graphql-results.xml'
            }
        }

        stage('Publish Reports') {
            steps {
                junit 'reports/*.xml'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
            publishHTML(target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'test-results',
                reportFiles: 'index.html',
                reportName: 'Test Results'
            ])
        }
    }
}