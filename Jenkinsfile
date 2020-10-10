pipeline {
    /* insert Declarative Pipeline here */
    agent none
    stages {
        stage('Build single EXE') {
            agent { label 'w10 && python' }
            steps {
                
                sh 'mvn -B clean verify'
            }
        }
        stage('Deploy to test vMix') {
            agent { label 'vMix'}
            steps {
                sh 'mvn -B clean verify'
            }
        }
    }
}