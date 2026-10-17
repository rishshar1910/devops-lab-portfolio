# Exercise 5: Docker Security with AppArmor and Python

## Objective
Secure a Docker container with an AppArmor profile, apply the profile with both the Docker CLI and the Docker SDK for Python, and test that restricted actions are blocked.

## Where this was run
AppArmor is a Linux kernel feature. This exercise could not run on my machine (Windows 11 with Docker Desktop):
- Docker Desktop's Linux VM reports only `seccomp` and `cgroupns` as security options (no `apparmor`).
- The WSL2 kernel has AppArmor compiled in, but disabled (`/sys/module/apparmor/parameters/enabled` is `N`).

So the exercise runs on a GitHub-hosted Ubuntu runner, which has AppArmor enabled. The workflow is [`.github/workflows/exercise-05-apparmor.yml`](../../.github/workflows/exercise-05-apparmor.yml), and each step is named after the task it covers. The output below comes from that run.

- Runner: Ubuntu 24.04.5, kernel `6.17.0-1022-azure`
- AppArmor: enabled (`Y`), module loaded, 123 profiles loaded, AppArmor 4.0.1 utilities

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask application (port 5000) |
| `Dockerfile` | Container image (`flask-apparmor`) |
| `my-apparmor-profile` | The AppArmor profile |
| `apply_apparmor.py` | Task 4: builds the image and applies the profile with the Docker SDK |
| `test_restricted_actions.py` | Task 5: the exercise's restricted-action test |
| `extra_checks.py` | My additional checks (see below) |

## The AppArmor profile
Key rules (the full file is `my-apparmor-profile`):

    profile my-apparmor-profile flags=(attach_disconnected,mediate_deleted) {
      #include <abstractions/base>

      network inet,                      # Flask can listen on TCP
      network inet6,
      network unix,

      capability,
      deny capability sys_admin,         # explicitly deny sys_admin

      file,                              # allowed by default, then denied below
      deny /etc/passwd r,                # sensitive system files
      deny /etc/shadow r,
      deny /etc/group r,
      deny /etc/gshadow r,
      deny /etc/** w,
      deny /var/** w,

      deny /bin/** x,                    # no executing binaries in system dirs
      deny /sbin/** x,
      deny /usr/bin/** x,
      deny /usr/sbin/** x,
      ...
    }

## Results

Profile loaded (Task 3), and the CLI run (Task 3c):

    $ sudo apparmor_parser -r /etc/apparmor.d/my-apparmor-profile
    $ sudo aa-status | grep my-apparmor-profile
       my-apparmor-profile

    $ docker run -d --name flask-cli --security-opt="apparmor=my-apparmor-profile" -p 5000:5000 flask-apparmor
    Profile reported by Docker: my-apparmor-profile
    Hello, this is a secure Flask application running inside a Docker container!

Docker SDK (Task 4, `apply_apparmor.py`):

    Container started: e593070f86a9
    AppArmor profile applied: ['apparmor=my-apparmor-profile']

Restricted actions (Task 5, `test_restricted_actions.py`):

    Container started: 5c1e60b11826
    Attempt to read /etc/passwd: Exit Code 1, Output: cat: /etc/passwd: Permission denied
    Attempt to execute /bin/bash: Exit Code 0, Output:
    Container stopped

Additional checks (`extra_checks.py`). A container with the profile is compared with a control container that has no profile (`apparmor=unconfined`):

    --- The app still works under the profile ---
    GET http://localhost:5000/ -> 'Hello, this is a secure Flask application running inside a Docker container!'

    --- With the AppArmor profile (should be blocked) ---
    [OK] python reads /etc/passwd: Exit Code 1, ... PermissionError: [Errno 13] Permission denied: '/etc/passwd'
    [OK] python writes /var/apparmor-test: Exit Code 1, ... PermissionError: [Errno 13] Permission denied: '/var/apparmor-test'
    [OK] python starts /bin/bash from inside the container: Exit Code 1, ... PermissionError: [Errno 13] Permission denied: '/bin/bash'
    [OK] python starts /usr/bin/id from inside the container: Exit Code 1, ... PermissionError: [Errno 13] Permission denied: '/usr/bin/id'
    [OK] python reads /app/app.py (allowed): Exit Code 0, Output: 'from flask import Flask ...'

    --- Control container without a profile (should work) ---
    [OK] cat /etc/passwd: Exit Code 0, Output: 'root:x:0:0:root:/root:/bin/bash ...'
    [OK] execute /bin/bash: Exit Code 0, Output: 'shell started'
    [OK] python reads /etc/passwd: Exit Code 0, Output: 'root:x:0:0:root:/root:/bin/bash ...'
    [OK] python starts /bin/bash from inside the container: Exit Code 0, Output: 'shell started'

    All extra checks passed

## What the results show
- **File access is restricted.** With the profile, reading `/etc/passwd` and writing under `/var` are denied. The same actions work in the control container, so the difference is the profile.
- **The application still works.** Flask serves requests on port 5000 under the profile.
- **Executing binaries is blocked when started from inside the container.** A process in the confined container (here Python) cannot launch `/bin/bash` or `/usr/bin/id`. This is the scenario the exec rules protect against, for example an exploited web app trying to spawn a shell.

## Differences from the exercise text
- **Profile definition.** The exercise's profile is declared as `/usr/bin/python3 { ... }`, so Docker cannot find a profile named `my-apparmor-profile`. Its blanket `deny /etc/** r` also stops Python from starting (it needs `/etc/ld.so.cache`). I rewrote it as a named profile, `profile my-apparmor-profile`, that keeps the same intent: deny sensitive `/etc` and `/var` access, deny executing binaries in `/bin` and `/usr/bin`, allow networking, deny `sys_admin`.
- **`docker exec` and the exit code 126.** The exercise's expected output shows `/bin/bash` failing with exit code 126. Here it returned 0, and `cat` itself ran (it only failed to read the file). The profile is applied to the process Docker launches, and the first program of a `docker exec` starts before the profile takes effect, so the exec rules did not stop it. The exec rules do apply to programs launched from inside the confined container, which `extra_checks.py` demonstrates. The `/etc/passwd` read denial (exit code 1) does match the exercise's expected output.
- **Environment.** The run used a GitHub Actions Ubuntu runner instead of a local Linux machine (see above).
- **Kernel denial log.** The workflow also tries to print `apparmor="DENIED"` lines from `dmesg` and the journal, but the runner exposed none, so no kernel-level denial messages are included here.
- **Flask version.** The Dockerfile's unpinned `pip install flask` resolved to Flask 3.0.3 on `python:3.8-slim`.
