# Exercise 9: Jenkins Multi-Stage Pipeline

## Objective

Create and run a Jenkins Pipeline with several stages (Build, Test, Deploy, Run Application, Test Application) for a small Python Flask application. The Jenkinsfile is loaded from a Git repository ("Pipeline script from SCM").

## Files

- `app.py`: Flask app that returns `Hello, Jenkins Multi-Stage Pipeline!` on `/`.
- `requirements.txt`: `flask==2.1.2`.
- `test_app.py`: unit test for the `/` route.
- `Jenkinsfile`: the pipeline from the exercise, unchanged.
- `README.md`: this file.

The files in this folder are copies of what lives in https://github.com/rishshar1910/devops-sample-code (commit `b206cc1`), the repository Jenkins pulls from.

## Steps and Results

### Step 1: Jenkins and the Pipeline plugin

Jenkins was the container from Exercise 7 (`jenkins/jenkins:lts`, Jenkins 2.580.1), restarted with `docker start jenkins` because Docker Desktop had been closed.

The Pipeline plugin turned out not to be working. Build #1 (below) failed because Jenkins did not know the `pipeline` step. The Jenkins log of the Exercise 7 setup wizard showed why: several plugin downloads from updates.jenkins.io had failed, and the Declarative Pipeline plugins depend on them:

    SEVERE  Failed to install snakeyaml-api
    Caused: java.io.IOException: Failed to load https://updates.jenkins.io/download/plugins/snakeyaml-api/2.7-152.vc672728cf536/snakeyaml-api.hpi to /var/jenkins_home/plugins/snakeyaml-api.jpi.tmp
    SEVERE  Failed to install jackson2-api
    SEVERE  Failed to install gradle
    SEVERE  Failed to install pipeline-model-api
    java.io.IOException: Failed to load: Pipeline: Model API (pipeline-model-api 2.2293.v6e7193cec599)
     - Failed to load: Jackson 2 API Plugin (jackson2-api 2.22.3-447.v6a_93ce7d2c82)

The plugin files existed on disk but could not be loaded:

    PS> docker exec jenkins bash -c "ls /var/jenkins_home/plugins | grep -E 'pipeline-model|workflow-aggregator'"
    pipeline-model-api
    pipeline-model-api.jpi
    pipeline-model-definition
    pipeline-model-definition.jpi
    pipeline-model-extensions
    pipeline-model-extensions.jpi
    workflow-aggregator
    workflow-aggregator.jpi

The missing plugins were re-installed (the Pipeline plugin and its dependency chain) and Jenkins was restarted. After that, builds ran the Declarative stages.

### Step 2: Create the application files

`app.py`, `requirements.txt` and `test_app.py` were created exactly as in the exercise, with Unix line endings (written with `[System.IO.File]::WriteAllText` and `\n`), in the existing `devops-sample-code` clone, together with the `Jenkinsfile` from the exercise:

    PS C:\Users\muksh\Documents\devops-sample-code> Get-ChildItem
    -a----        10/18/2026  10:47 PM            178 app.py
    -a----        10/18/2026  12:17 PM             35 hello-world.sh
    -a----        10/18/2026  10:47 PM           1412 Jenkinsfile
    -a----        10/18/2026  10:47 PM             13 requirements.txt
    -a----        10/18/2026  10:47 PM            407 test_app.py

### Step 3: Commit and push to GitHub

    PS> git add app.py requirements.txt test_app.py
    PS> git commit -m "Initial commit"
    [main ff07667] Initial commit
     3 files changed, 24 insertions(+)
    PS> git add Jenkinsfile
    PS> git commit -m "Added Jenkinsfile"
    [main b206cc1] Added Jenkinsfile
     1 file changed, 52 insertions(+)
    PS> git ls-files --eol
    i/lf    w/lf    attr/                   Jenkinsfile
    i/lf    w/lf    attr/                   app.py
    i/lf    w/lf    attr/                   hello-world.sh
    i/lf    w/lf    attr/                   requirements.txt
    i/lf    w/lf    attr/                   test_app.py
    PS> git -c credential.helper= push origin main
    To https://github.com/rishshar1910/devops-sample-code.git
       1c64a31..b206cc1  main -> main

All files are stored with Unix line endings (`i/lf`). A Windows line ending inside the Jenkinsfile's multi-line `sh` blocks would have broken the shell commands.

### Step 4: Create the Jenkins job

New Item, name `Python-MultiStage-Pipeline`, type Pipeline. Under Pipeline: Definition `Pipeline script from SCM`, SCM `Git`, Repository URL `https://github.com/rishshar1910/devops-sample-code.git`, no credentials (public repository), Branch Specifier `*/main`, Script Path `Jenkinsfile`. Saved and built with Build Now.

### Step 5: Build #1 failed: Declarative Pipeline not available

The checkout worked (`Obtained Jenkinsfile from git ...`), but the Jenkinsfile could not run:

    [Pipeline] Start of Pipeline
    java.lang.NoSuchMethodError: No such DSL method 'pipeline' found among steps [archive, bat, build, ...]
        at WorkflowScript.run(WorkflowScript:1)
    Finished: FAILURE

This was the broken Pipeline plugin described in Step 1.

### Step 6: Build #2 failed: Python missing (the exercise's expected error)

With the Pipeline plugin working, build #2 checked out commit `b206cc1`, ran the Build stage and failed in Test, as the exercise predicts:

    [Pipeline] { (Test)
    Running tests...
    + python3 -m unittest discover -s .
    .../script.sh.copy: 1: python3: not found
    [Pipeline] { (Deploy)
    Stage "Deploy" skipped due to earlier failure(s)
    [Pipeline] { (Run Application)
    Stage "Run Application" skipped due to earlier failure(s)
    [Pipeline] { (Test Application)
    Stage "Test Application" skipped due to earlier failure(s)
    [Pipeline] { (Declarative: Post Actions)
    Pipeline failed. Check the logs for more details.
    ERROR: script returned exit code 127
    Finished: FAILURE

### Step 7: Install Python in the Jenkins container (the exercise's "Handling build errors")

    PS> docker exec -u root jenkins bash -c "apt-get update && apt-get install -y python3 python3-pip python3-venv python3-flask"
    ...
    The following NEW packages will be installed:
      ... python3 python3-flask python3-pip python3-venv ...
    2 upgraded, 104 newly installed, 0 to remove and 5 not upgraded.
    PS> docker exec jenkins python3 --version
    Python 3.13.5
    PS> docker exec jenkins python3 -c "from importlib.metadata import version; print('flask', version('flask'))"
    flask 3.1.1

### Step 8: Build #3 succeeded

Console log of build #3 (read from the Jenkins container; Jenkins' hidden console annotations were removed):

    Started by user admin
    Obtained Jenkinsfile from git https://github.com/rishshar1910/devops-sample-code.git
    [Pipeline] Start of Pipeline
    [Pipeline] node
    Running on Jenkins in /var/jenkins_home/workspace/Python-MultiStage-Pipeline
    [Pipeline] {
    [Pipeline] stage
    [Pipeline] { (Declarative: Checkout SCM)
    [Pipeline] checkout
    Selected Git installation does not exist. Using Default
    The recommended git tool is: NONE
    No credentials specified
     > git rev-parse --resolve-git-dir /var/jenkins_home/workspace/Python-MultiStage-Pipeline/.git # timeout=10
    Fetching changes from the remote Git repository
     > git config remote.origin.url https://github.com/rishshar1910/devops-sample-code.git # timeout=10
    Fetching upstream changes from https://github.com/rishshar1910/devops-sample-code.git
     > git --version # timeout=10
     > git --version # 'git version 2.47.3'
     > git fetch --tags --force --progress -- https://github.com/rishshar1910/devops-sample-code.git +refs/heads/*:refs/remotes/origin/* # timeout=10
     > git rev-parse refs/remotes/origin/main^{commit} # timeout=10
    Checking out Revision b206cc1fa645fe932c46d684a426ddaae2f8932e (refs/remotes/origin/main)
     > git config core.sparsecheckout # timeout=10
     > git checkout -f b206cc1fa645fe932c46d684a426ddaae2f8932e # timeout=10
    Commit message: "Added Jenkinsfile"
     > git rev-list --no-walk b206cc1fa645fe932c46d684a426ddaae2f8932e # timeout=10
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] withEnv
    [Pipeline] {
    [Pipeline] stage
    [Pipeline] { (Build)
    [Pipeline] echo
    Creating virtual environment and installing dependencies...
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] stage
    [Pipeline] { (Test)
    [Pipeline] echo
    Running tests...
    [Pipeline] sh
    + python3 -m unittest discover -s .
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.006s

    OK
    Hello, Jenkins Multi-Stage Pipeline!
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] stage
    [Pipeline] { (Deploy)
    [Pipeline] echo
    Deploying application...
    [Pipeline] sh
    + mkdir -p /var/jenkins_home/workspace/Python-MultiStage-Pipeline/python-app-deploy
    + cp /var/jenkins_home/workspace/Python-MultiStage-Pipeline/app.py /var/jenkins_home/workspace/Python-MultiStage-Pipeline/python-app-deploy/
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] stage
    [Pipeline] { (Run Application)
    [Pipeline] echo
    Running application...
    [Pipeline] sh
    + + echo 1879
    nohup python3 /var/jenkins_home/workspace/Python-MultiStage-Pipeline/python-app-deploy/app.py
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] stage
    [Pipeline] { (Test Application)
    [Pipeline] echo
    Testing application...
    [Pipeline] sh
    + python3 /var/jenkins_home/workspace/Python-MultiStage-Pipeline/test_app.py
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.006s

    OK
    Hello, Jenkins Multi-Stage Pipeline!
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] stage
    [Pipeline] { (Declarative: Post Actions)
    [Pipeline] echo
    Pipeline completed successfully!
    [Pipeline] }
    [Pipeline] // stage
    [Pipeline] }
    [Pipeline] // withEnv
    [Pipeline] }
    [Pipeline] // node
    [Pipeline] End of Pipeline
    Finished: SUCCESS

The Deploy stage created the deployment folder inside the Jenkins workspace:

    PS> docker exec jenkins ls -l /var/jenkins_home/workspace/Python-MultiStage-Pipeline/python-app-deploy
    total 12
    -rw-r--r-- 1 jenkins jenkins 319 Oct 18 17:36 app.log
    -rw-r--r-- 1 jenkins jenkins   5 Oct 18 17:36 app.pid
    -rw-r--r-- 1 jenkins jenkins 178 Oct 18 17:36 app.py

`app.pid` holds the process ID printed in the log (`1879`), and the copy of `app.py` is the same size (178 bytes) as the one in the repository.

## Differences from the exercise instructions

- **Repository:** the exercise says to `mkdir python-flask-app`, run `git init` and add the remote `devops-sample-code`. That repository already existed from Exercise 8 (it holds `hello-world.sh`), so the files were added to the existing clone, at the repository root, which is where the Jenkinsfile expects `app.py` and `test_app.py`. `git init` and `git remote add` were not needed.
- **One push:** the two commits (`Initial commit`, `Added Jenkinsfile`) were pushed together with one `git push` instead of two pushes. The push used `git -c credential.helper= push origin main` with a fine-grained personal access token, as in Exercise 8.
- **Line endings:** the files were written with Unix line endings (and verified with `git ls-files --eol`) because the Jenkinsfile contains multi-line shell blocks.
- **Branch:** `*/main` as the Branch Specifier (Jenkins defaults to `*/master`).
- **Pipeline plugin (Step 1 of the exercise):** it was not working, because plugin downloads had failed during the Exercise 7 setup. This showed up as build #1 failing with `No such DSL method 'pipeline'`, before the Python errors the exercise describes. The plugins were re-installed and Jenkins restarted.
- **Python packages (the exercise's Step 8):** the exercise lists `python3`, `pip`, `python3.11-venv` and `python3-flask`. The Jenkins image is based on Debian trixie, which has Python 3.13, so `python3.11-venv` does not exist and the pip package is called `python3-pip`. The command used was `docker exec -u root jenkins bash -c "apt-get update && apt-get install -y python3 python3-pip python3-venv python3-flask"` (non-interactive, instead of an interactive shell in the container). `apt` also installed about 100 recommended packages (compilers and so on).
- **Flask version:** the Build stage in the exercise's Jenkinsfile only prints a message; it does not run `pip install -r requirements.txt`, even though the "Expected Outcome" text says it does. The Jenkinsfile was used unchanged, so the tests ran against Flask 3.1.1 from `python3-flask`, not `flask==2.1.2` from `requirements.txt`.
- **Deploy location:** the "Expected Outcome" text says `app.py` is copied to `/tmp/python-app-deploy`, but the Jenkinsfile copies it to `${WORKSPACE}/python-app-deploy` (and the exercise's sample log shows the same). The Jenkinsfile was followed.
- **Job name:** `Python-MultiStage-Pipeline`, the exercise's example name.
- **Log:** the raw Jenkins log contains hidden annotation text (`ha:////...`) that the web UI does not show; it was removed from the log above. Build #1 and #2 logs are shortened.
- **Not done:** the optional "Additional Enhancements" (flake8/pylint stage, Docker deployment, notifications) were not part of the required steps and were not implemented.

## Cleanup

The Jenkins container, the `Python-MultiStage-Pipeline` job and the installed Python packages are left in place for the next exercise. To remove the container: `docker rm -f jenkins`. Revoke the fine-grained GitHub token when it is no longer needed.
