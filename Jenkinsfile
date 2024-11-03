pipeline {
    agent any 

    stages {
        stage('Checkout') {
            steps {
                // Checkout code from GitHub
                git url: 'https://github.com/PrachiiBB/stress_testing.git', branch: 'main'
            }
        }
    }
}
