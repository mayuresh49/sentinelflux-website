pipeline {
    agent any

    // ── Build parameters ─────────────────────────────────────────────────────
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
        booleanParam(name: 'RUN_WEB_LOGIN',  defaultValue: true,  description: 'Login UI suite')
        booleanParam(name: 'RUN_WEB_PIM',    defaultValue: true,  description: 'PIM Employee UI suite')
        booleanParam(name: 'RUN_WEB_LEAVE',  defaultValue: true,  description: 'Leave List UI suite')
        booleanParam(name: 'RUN_WEB_ADMIN',  defaultValue: true,  description: 'Admin Users UI suite')
        booleanParam(name: 'RUN_API',        defaultValue: false, description: 'Restful Booker REST API suite')
        booleanParam(name: 'RUN_API_LEAVE',  defaultValue: false, description: 'OrangeHRM Leave API suite')
        booleanParam(name: 'RUN_API_ADMIN',  defaultValue: false, description: 'OrangeHRM Admin Users API suite')

        // ReportPortal — requires Jenkins credential 'rp-api-key' (Secret Text) to be configured.
        // Set ENABLE_RP=false (default) to run without RP; results are still in HTML + JUnit XML.
        booleanParam(
            name: 'ENABLE_RP',
            defaultValue: false,
            description: 'Send results to ReportPortal (requires rp-api-key Jenkins credential)'
        )
    }

    environment {
        VENV_PYTEST = 'venv/bin/pytest'
        // --override-ini strips the default --html from pytest.ini addopts so each
        // parallel suite stage writes its own named report without file-write races.
        // --tracing=retain-on-failure captures Playwright network + browser trace on failure.
        CI_ADDOPTS = '-ra -q --screenshot=on --video=retain-on-failure --tracing=retain-on-failure'
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        ansiColor('xterm')
    }

    // ── Stages ───────────────────────────────────────────────────────────────
    stages {

        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install -r requirements.txt -q
                    venv/bin/playwright install chromium firefox webkit
                    mkdir -p reports/artifacts test-results
                '''
            }
        }

        // Inject RP API key from Jenkins credentials store when ENABLE_RP is true.
        // The credential ID must be 'rp-api-key' (Secret Text). If it is not
        // configured in Jenkins this stage is skipped and RP reporting is disabled.
        stage('Inject RP Credentials') {
            when { expression { return params.ENABLE_RP } }
            steps {
                script {
                    try {
                        withCredentials([string(credentialsId: 'rp-api-key', variable: 'RP_KEY')]) {
                            env.RP_API_KEY = env.RP_KEY
                        }
                        echo 'ReportPortal credentials loaded.'
                    } catch (Exception e) {
                        echo "WARNING: 'rp-api-key' credential not found in Jenkins — RP reporting disabled."
                        env.RP_API_KEY = ''
                    }
                }
            }
        }

        // Suites run as parallel Jenkins stages; xdist provides per-suite test-level parallelism.
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

                stage('Leave UI') {
                    when { expression { return params.RUN_WEB_LEAVE } }
                    steps {
                        script {
                            def sessionFlag = params.SESSION_LOGIN ? '--session-login' : ''
                            sh """
                                ${env.VENV_PYTEST} tests/web/test_leave.py \\
                                  -m web \\
                                  --env=${params.ENV} \\
                                  --browser=${params.BROWSER} \\
                                  -n ${params.PARALLEL_COUNT} \\
                                  ${sessionFlag} \\
                                  --override-ini="addopts=${env.CI_ADDOPTS}" \\
                                  --html=reports/leave-report.html \\
                                  --self-contained-html \\
                                  --junitxml=reports/leave-results.xml
                            """
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/leave-results.xml'
                        }
                    }
                }

                stage('Admin Users UI') {
                    when { expression { return params.RUN_WEB_ADMIN } }
                    steps {
                        script {
                            def sessionFlag = params.SESSION_LOGIN ? '--session-login' : ''
                            sh """
                                ${env.VENV_PYTEST} tests/web/test_admin_users.py \\
                                  -m web \\
                                  --env=${params.ENV} \\
                                  --browser=${params.BROWSER} \\
                                  -n ${params.PARALLEL_COUNT} \\
                                  ${sessionFlag} \\
                                  --override-ini="addopts=${env.CI_ADDOPTS}" \\
                                  --html=reports/admin-report.html \\
                                  --self-contained-html \\
                                  --junitxml=reports/admin-results.xml
                            """
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/admin-results.xml'
                        }
                    }
                }

                stage('API') {
                    when { expression { return params.RUN_API } }
                    steps {
                        sh """
                            ${env.VENV_PYTEST} tests/api/test_rest_api.py tests/api/test_graphql_api.py \\
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

                stage('Leave API') {
                    when { expression { return params.RUN_API_LEAVE } }
                    steps {
                        sh """
                            ${env.VENV_PYTEST} tests/api/test_orangehrm_leave.py \\
                              -m api \\
                              --env=${params.ENV} \\
                              --override-ini="addopts=${env.CI_ADDOPTS}" \\
                              --html=reports/leave-api-report.html \\
                              --self-contained-html \\
                              --junitxml=reports/leave-api-results.xml
                        """
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/leave-api-results.xml'
                        }
                    }
                }

                stage('Admin API') {
                    when { expression { return params.RUN_API_ADMIN } }
                    steps {
                        sh """
                            ${env.VENV_PYTEST} tests/api/test_orangehrm_admin.py \\
                              -m api \\
                              --env=${params.ENV} \\
                              --override-ini="addopts=${env.CI_ADDOPTS}" \\
                              --html=reports/admin-api-report.html \\
                              --self-contained-html \\
                              --junitxml=reports/admin-api-results.xml
                        """
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/admin-api-results.xml'
                        }
                    }
                }

            }
        }
    }

    // ── Post-run artifacts and reporting ─────────────────────────────────────
    post {
        always {
            // Collected on every run:
            //   reports/artifacts/**        — full-page screenshots, console.log, trace.zip (conftest hook)
            //   test-results/**             — pytest-playwright: viewport screenshot, video.webm, trace.zip
            //   reports/*.html              — per-suite HTML reports
            //   reports/*.xml               — JUnit XML (Jenkins test trend graphs)
            archiveArtifacts(
                artifacts: 'reports/**, test-results/**',
                allowEmptyArchive: true
            )

            // Requires "HTML Publisher" Jenkins plugin
            publishHTML(target: [
                allowMissing:          true,
                alwaysLinkToLastBuild: true,
                keepAll:               true,
                reportDir:             'reports',
                reportFiles:           'login-report.html,pim-report.html,leave-report.html,admin-report.html,api-report.html,leave-api-report.html,admin-api-report.html',
                reportName:            'SentinelFlux Test Reports'
            ])
        }
        failure {
            echo 'One or more suites failed — check the Reports tab, archived artifacts, and trace.playwright.dev for trace.zip files'
        }
    }
}
