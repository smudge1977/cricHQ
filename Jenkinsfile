pipeline {
  agent none
  stages {
    stage('Build single EXE') {
      agent {
        label 'w10 && python'
      }
      steps {
        bat(script: 'packaging/build.cmd', returnStdout: true)
      }
    }

    stage('Deploy to test vMix') {
      agent {
        label 'vMix'
      }
      steps {
        sh 'mvn -B clean verify'
      }
    }

  }
}