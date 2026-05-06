pipeline {
    agent any

    // ── Build parameters ────────────────────────────────────────────────────
    parameters {
        choice(
            name: 'ENV',
            choices: ['qa', 'staging', 'prod'],
            description: 'Target environment — maps to config/env_<ENV>.yaml'
        )
        choice(
            name: 'BROWSER',
            choices: ['chromium', 'firefox', 'webkit'],
            description: 'Playwright browser'
        )
        choice(
            name: 'PARALLEL_COUNT',
            choices: ['4', '2', '1', '8'],
            description: 'pytest-xdist workers per suite stage'
        )
        booleanParam(
            name: 'SESSION_LOGIN',
            defaultValue: true,
            description: 'Reuse one authenticated browser session per xdist worker (--session-login)'
        )

        // Suite toggles
        booleanParam(name: 'RUN_WEB_LOGIN', defaultValue: true,  description: 'Login UI suite')
        booleanParam(name: 'RUN_WEB_PIM',   defaultValue: true,  description: 'PIM Employee UI suite')
        booleanParam(name: 'RUN_API',        defaultValue: false, description: 'REST API suite')
    }

    environment {
        VENV_PYTEST = 'venv/bin/pytest'
        // Overrides pytest.ini addopts so each suite writes its own --html report
        // without parallel stages racing to write the same reports/report.html
        CI_ADDOPTS   = '-ra -q --screenshot=on --video=retain-on-failure'
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        ansiColor('xterm')
    }

    // ── Stages ──────────────────────────────────────────────────────────────
    stages {

        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install -r requirements.txt -q
                    venv/bin/playwright install chromium firefox webkit
                    mkdir -p reports
                '''
            }
        }

        // Suites run in parallel Jenkins stages; xdist handles per-suite parallelism
        stage('Test Suites') {
            parallel {

                stage('Login') {
                    when { expression { return params.RUN_WEB_LOGIN } }
                    steps {
                        script {
                            def sessionFlag = params.SESSION_LOGIN ? '--session-login' : ''
                            sh """
                                ${env.VENV_PYTEST} tests/web/test_login.py \\
                                  -m web \\
                                  --env=${params.ENV} \\
                                  --browser=${params.BROWSER} \\
                                  -n ${params.PARALLEL_COUNT} \\
                                  ${sessionFlag} \\
                                  --override-ini="addopts=${env.CI_ADDOPTS}" \\
                                  --html=reports/login-report.html \\
                                  --self-contained-html \\
                                  --junitxml=reports/login-results.xml
                            """
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/login-results.xml'
                        }
                    }
                }

                stage('PIM Employee') {
                    when { expression { return params.RUN_WEB_PIM } }
                    steps {
                        script {
                            def sessionFlag = params.SESSION_LOGIN ? '--session-login' : ''
                            sh """
                                ${env.VENV_PYTEST} tests/web/test_pim_employee.py \\
                                  -m web \\
                                  --env=${params.ENV} \\
                                  --browser=${params.BROWSER} \\
                                  -n ${params.PARALLEL_COUNT} \\
                                  ${sessionFlag} \\
                                  --override-ini="addopts=${env.CI_ADDOPTS}" \\
                                  --html=reports/pim-report.html \\
                                  --self-contained-html \\
                                  --junitxml=reports/pim-results.xml
                            """
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/pim-results.xml'
                        }
                    }
                }

                stage('API') {
                    when { expression { return params.RUN_API } }
                    steps {
                        sh """
                            ${env.VENV_PYTEST} tests/api/ \\
                              -m api \\
                              --env=${params.ENV} \\
                              -n ${params.PARALLEL_COUNT} \\
                              --override-ini="addopts=${env.CI_ADDOPTS}" \\
                              --html=reports/api-report.html \\
                              --self-contained-html \\
                              --junitxml=reports/api-results.xml
                        """
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/api-results.xml'
                        }
                    }
                }

            }
        }
    }

    // ── Post-run ─────────────────────────────────────────────────────────────
    post {
        always {
            // Screenshots and videos from failed tests
            archiveArtifacts artifacts: 'reports/**, test-results/**', allowEmptyArchive: true

            // Requires "HTML Publisher" Jenkins plugin
            publishHTML(target: [
                allowMissing:          true,
                alwaysLinkToLastBuild: true,
                keepAll:               true,
                reportDir:             'reports',
                reportFiles:           'login-report.html,pim-report.html,api-report.html',
                reportName:            'SentinelFlux Test Reports'
            ])
        }
        failure {
            echo 'One or more suites failed — check Reports tab and archived artifacts'
        }
    }
}
