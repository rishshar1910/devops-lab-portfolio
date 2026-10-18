# Exercise 8: Jenkins Hello World Job

## Objective

Create a "Hello World" shell script, push it to its own public GitHub repository (devops-sample-code), and create a Jenkins Freestyle job named HelloWorld that pulls the script from that repository and runs it with `sh hello-world.sh`.

## Files

- `hello-world.sh`: a copy of the script that lives in https://github.com/rishshar1910/devops-sample-code (the repository Jenkins pulls from).
- `README.md`: this file.

## Steps and Results

### Step 1: Create the script and push it to GitHub

The repository `devops-sample-code` was created in the browser (public, description "A demo repository for Jenkins scripting.", no initial files). A fine-grained personal access token was created for it (step 1b) and used at the push prompt. The token is not stored anywhere in this repository.

Create the script (Unix line endings), initialize the repository, add the script and commit:

    PS C:\Users\muksh\Documents\devops-sample-code> New-Item hello-world.sh -ItemType File
    PS C:\Users\muksh\Documents\devops-sample-code> [System.IO.File]::WriteAllText("$PWD\hello-world.sh", "#!/bin/bash`necho `"Hello, Jenkins!`"`n")
    PS C:\Users\muksh\Documents\devops-sample-code> Get-Content hello-world.sh
    #!/bin/bash
    echo "Hello, Jenkins!"
    PS C:\Users\muksh\Documents\devops-sample-code> git init -b main
    Initialized empty Git repository in C:/Users/muksh/Documents/devops-sample-code/.git/
    PS C:\Users\muksh\Documents\devops-sample-code> git add hello-world.sh
    warning: in the working copy of 'hello-world.sh', LF will be replaced by CRLF the next time Git touches it
    PS C:\Users\muksh\Documents\devops-sample-code> git status
    On branch main

    No commits yet

    Changes to be committed:
      (use "git rm --cached <file>..." to unstage)
            new file:   hello-world.sh

    PS C:\Users\muksh\Documents\devops-sample-code> git commit -m "Add hello-world.sh"
    [main (root-commit) 1c64a31] Add hello-world.sh
     1 file changed, 2 insertions(+)
     create mode 100644 hello-world.sh
    PS C:\Users\muksh\Documents\devops-sample-code> git remote add origin https://github.com/rishshar1910/devops-sample-code.git

Push to GitHub. The first attempt was rejected by GitHub:

    PS C:\Users\muksh\Documents\devops-sample-code> git -c credential.helper= push -u origin main
    Username for 'https://github.com': rishshar1910
    Password for 'https://rishshar1910@github.com':
    remote: Invalid username or token. Password authentication is not supported for Git operations.
    fatal: Authentication failed for 'https://github.com/rishshar1910/devops-sample-code.git/'

The same command was run again, entering the token at the password prompt, and succeeded:

    PS C:\Users\muksh\Documents\devops-sample-code> git -c credential.helper= push -u origin main
    Username for 'https://github.com': rishshar1910
    Password for 'https://rishshar1910@github.com':
    Enumerating objects: 3, done.
    Counting objects: 100% (3/3), done.
    Writing objects: 100% (3/3), 265 bytes | 265.00 KiB/s, done.
    Total 3 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
    To https://github.com/rishshar1910/devops-sample-code.git
     * [new branch]      main -> main
    branch 'main' set up to track 'origin/main'.

### Step 2: Verify the repository and the committed file

    PS C:\Users\muksh\Documents\devops-sample-code> git ls-files --eol
    i/lf    w/lf    attr/                   hello-world.sh
    PS C:\Users\muksh\Documents\devops-sample-code> git log --oneline -n 3
    1c64a31 (HEAD -> main, origin/main) Add hello-world.sh
    PS C:\Users\muksh\Documents\devops-sample-code> git remote -v
    origin  https://github.com/rishshar1910/devops-sample-code.git (fetch)
    origin  https://github.com/rishshar1910/devops-sample-code.git (push)

`i/lf` shows that the committed script uses Unix line endings.

### Step 3: Ensure Jenkins is running

The Jenkins container from Exercise 7 was still running:

    PS C:\Users\muksh> docker ps --filter name=jenkins
    CONTAINER ID   IMAGE                 COMMAND                  CREATED          STATUS          PORTS                                                                                          NAMES
    39d96ef4cd7c   jenkins/jenkins:lts   "/usr/bin/tini -- /u?"   33 minutes ago   Up 33 minutes   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp, 0.0.0.0:50000->50000/tcp, [::]:50000->50000/tcp   jenkins
    PS C:\Users\muksh> curl.exe -s -o NUL -w "Jenkins HTTP status: %{http_code}`n" http://localhost:8080/login
    Jenkins HTTP status: 200

### Step 4: Create and configure the Jenkins job

In the Jenkins UI at http://localhost:8080:

1. New Item, name `HelloWorld`, type Freestyle project, OK.
2. Description: `Hello World! Jenkins job.`
3. Source Code Management: Git, Repository URL `https://github.com/rishshar1910/devops-sample-code.git`, Branch Specifier `*/main`.
4. Build: Add build step, Execute shell, command `sh hello-world.sh`.
5. Save, then Build Now.

### Step 5: Build output

The console log of build #1, read from the Jenkins container:

    PS C:\Users\muksh\Documents\devops-sample-code> docker exec jenkins cat /var/jenkins_home/jobs/HelloWorld/builds/1/log
    Started by user ha:////4FIrWY8U2HmwhtO31D1EE4siEaUeG1SOLq2nktDmjEizAAAAlx+LCAAAAAAAAP9b85aBtbiIQTGjNKU4P08vOT+vOD8nVc83PyU1x6OyILUoJzMv2y+/JJUBAhiZGBgqihhk0NSjKDWzXb3RdlLBUSYGJk8GtpzUvPSSDB8G5tKinBIGIZ+sxLJE/ZzEvHT94JKizLx0a6BxUmjGOUNodHsLgAzWEgZu/dLi1CL9xJTczDwAj6GcLcAAAAA=admin
    Running as SYSTEM
    Building in workspace /var/jenkins_home/workspace/HelloWorld
    The recommended git tool is: NONE
    No credentials specified
    Cloning the remote Git repository
    Cloning repository https://github.com/rishshar1910/devops-sample-code.git
     > git init /var/jenkins_home/workspace/HelloWorld # timeout=10
    Fetching upstream changes from https://github.com/rishshar1910/devops-sample-code.git
     > git --version # timeout=10
     > git --version # 'git version 2.47.3'
     > git fetch --tags --force --progress -- https://github.com/rishshar1910/devops-sample-code.git +refs/heads/*:refs/remotes/origin/* # timeout=10
     > git config remote.origin.url https://github.com/rishshar1910/devops-sample-code.git # timeout=10
     > git config --add remote.origin.fetch +refs/heads/*:refs/remotes/origin/* # timeout=10
    Avoid second fetch
     > git rev-parse refs/remotes/origin/main^{commit} # timeout=10
    Checking out Revision 1c64a31454e09532434225f9866067193cf4d754 (refs/remotes/origin/main)
     > git config core.sparsecheckout # timeout=10
     > git checkout -f 1c64a31454e09532434225f9866067193cf4d754 # timeout=10
    Commit message: "Add hello-world.sh"
    First time build. Skipping changelog.
    [HelloWorld] $ /bin/sh -xe /tmp/jenkins9406417458221745767.sh
    + sh hello-world.sh
    Hello, Jenkins!
    Finished: SUCCESS

The first line is the raw log: Jenkins stores the user as an encoded link, and the web UI shows it as `Started by user admin`. The job checked out commit `1c64a31`, the same commit that was pushed in Step 1, and printed `Hello, Jenkins!`.

## Differences from the exercise instructions

- `git config --global user.name/user.email` was skipped, because both were already set on this machine.
- `chmod +x hello-world.sh` was skipped. Windows has no executable bit, and the job runs the script as `sh hello-world.sh`, so it is not needed.
- `git init -b main` was used instead of `git init`, so the branch is called `main` and `git push -u origin main` works as written (the brief's sample output shows `master`).
- The script was written with `[System.IO.File]::WriteAllText` instead of vim or notepad, so it has Unix line endings (no stray carriage return in Jenkins' output).
- The push used `git -c credential.helper= push -u origin main`, so Git Credential Manager did not reuse a saved login and the token was entered at the prompt, as in the brief. The first attempt was rejected and the second succeeded (see Step 1).
- The Branch Specifier in the Jenkins job is `*/main` instead of Jenkins' default `*/master`, because the repository's branch is `main`.
- The brief's repository URLs contain placeholders, and step 7 has a typo (`.../DevOps`). The real URL `https://github.com/rishshar1910/devops-sample-code` was used.
- The log shows `Started by user admin` instead of the brief's `Admin`, and it contains the Git checkout lines that Jenkins prints when a Git repository is configured, which are not in the brief's sample.
- Added to the brief: a copy of `hello-world.sh` in this folder. No screenshot was taken, because the brief does not ask for one.

## Cleanup

The HelloWorld job and the Jenkins container are left in place for the next exercises. Revoke the fine-grained token when it is no longer needed: GitHub, Settings, Developer settings, Personal access tokens, Fine-grained tokens, Delete.
