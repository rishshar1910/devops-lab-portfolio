import sys
import time
import urllib.request

import docker

# Extra checks (not part of the original exercise): confirm the app still works
# under the profile, and compare against a container with no profile.
client = docker.from_env()
failures = []


def run(container, cmd):
    try:
        code, out = container.exec_run(cmd)
        return code, out.decode(errors="replace").strip()
    except docker.errors.APIError as err:
        return 126, f"APIError: {err.explanation or err}"


def attempt(label, container, cmd, expect_blocked):
    code, output = run(container, cmd)
    blocked = code != 0
    verdict = "OK" if blocked == expect_blocked else "UNEXPECTED"
    if verdict == "UNEXPECTED":
        failures.append(label)
    print(f"[{verdict}] {label}: Exit Code {code}, Output: {output[:150]!r}")


confined = client.containers.run(
    "flask-apparmor",
    ports={'5000/tcp': 5000},
    security_opt=["apparmor=my-apparmor-profile"],
    detach=True,
)
control = client.containers.run(
    "flask-apparmor",
    security_opt=["apparmor=unconfined"],
    detach=True,
)

try:
    print("--- The app still works under the profile ---")
    body = None
    for _ in range(15):
        try:
            body = urllib.request.urlopen("http://localhost:5000/", timeout=2).read().decode()
            break
        except Exception:
            time.sleep(1)
    print(f"GET http://localhost:5000/ -> {body!r}")
    if not body:
        failures.append("Flask app did not respond under the profile")

    print("\n--- With the AppArmor profile (should be blocked) ---")
    attempt("python reads /etc/passwd", confined,
            ["python", "-c", "print(open('/etc/passwd').read())"], True)
    attempt("python writes /var/apparmor-test", confined,
            ["python", "-c", "open('/var/apparmor-test', 'w').write('x')"], True)
    attempt("python reads /app/app.py (allowed)", confined,
            ["python", "-c", "print(open('/app/app.py').read()[:40])"], False)

    print("\n--- Control container without a profile (should work) ---")
    attempt("cat /etc/passwd", control, ["cat", "/etc/passwd"], False)
    attempt("execute /bin/bash", control, ["/bin/bash", "-c", "echo shell started"], False)
    attempt("python reads /etc/passwd", control,
            ["python", "-c", "print(open('/etc/passwd').read())"], False)
finally:
    for c in (confined, control):
        c.stop()
        c.remove()

if failures:
    print(f"\nFAILED checks: {failures}")
    sys.exit(1)
print("\nAll extra checks passed")
