# Exercise 3: Scaling a Flask App with ReplicaSets

## Objective
Understand ReplicaSets and Pods by running a Flask "flash sale" service, scaling it out, watching Kubernetes replace a deleted Pod, and observing how requests are spread across Pods.

## Prerequisites
- Docker Desktop
- kubectl
- Minikube v1.39.0 (single node, Kubernetes v1.37.0)

## Implementation
1. Wrote a Flask app (`app.py`) with three endpoints: `/` (welcome), `/buy` (simulated checkout, reports which Pod served it) and `/health` (used by the probes).
2. Wrote a `Dockerfile` that runs the app under gunicorn on port 5000.
3. Built the image `flashsale:1.0` and loaded it into Minikube with `minikube image load`.
4. Defined a ReplicaSet with 3 replicas, readiness and liveness probes on `/health`, and CPU/memory requests and limits, plus a ClusterIP Service (`flashsale-svc`).
5. Scaled the ReplicaSet from 3 to 5 replicas.
6. Deleted one Pod and watched the ReplicaSet create a replacement.
7. Called `/buy` through the Service from a temporary Pod inside the cluster to see which Pod served each request.

## Commands Used

    docker build -t flashsale:1.0 .
    minikube image load flashsale:1.0
    kubectl apply -f flashsale-replicaset.yaml
    kubectl get pods
    kubectl get rs
    kubectl scale rs flashsale-rs --replicas=5
    kubectl delete pod <pod-name>
    kubectl get pods -o wide
    kubectl run curl-test --rm -it --image=curlimages/curl --restart=Never -- sh -c 'for i in 1 2 3 4 5 6 7 8; do curl -s flashsale-svc/buy; echo; done'

## Output

Initial deployment, 3 replicas:

    $ kubectl get pods
    NAME                 READY   STATUS    RESTARTS   AGE
    flashsale-rs-kqgjv   1/1     Running   0          7s
    flashsale-rs-lhf4p   1/1     Running   0          7s
    flashsale-rs-qz88x   1/1     Running   0          7s

    $ kubectl get rs
    NAME           DESIRED   CURRENT   READY   AGE
    flashsale-rs   3         3         3       7s

After scaling to 5 replicas:

    $ kubectl scale rs flashsale-rs --replicas=5

    $ kubectl get rs
    NAME           DESIRED   CURRENT   READY   AGE
    flashsale-rs   5         5         5       81s

    $ kubectl get pods
    NAME                 READY   STATUS    RESTARTS   AGE
    flashsale-rs-kqgjv   1/1     Running   0          81s
    flashsale-rs-lhf4p   1/1     Running   0          81s
    flashsale-rs-nczxz   1/1     Running   0          7s
    flashsale-rs-nglpf   1/1     Running   0          7s
    flashsale-rs-qz88x   1/1     Running   0          81s

Self-healing: deleting `flashsale-rs-kqgjv` immediately creates a replacement (`flashsale-rs-2bbtq`):

    $ kubectl delete pod flashsale-rs-kqgjv
    pod "flashsale-rs-kqgjv" deleted from default namespace

    $ kubectl get pods
    NAME                 READY   STATUS    RESTARTS   AGE
    flashsale-rs-2bbtq   0/1     Running   0          1s
    flashsale-rs-lhf4p   1/1     Running   0          83s
    flashsale-rs-nczxz   1/1     Running   0          9s
    flashsale-rs-nglpf   1/1     Running   0          9s
    flashsale-rs-qz88x   1/1     Running   0          83s

Pod distribution (all Pods run on the single Minikube node):

    $ kubectl get pods -o wide
    NAME                 READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
    flashsale-rs-2bbtq   1/1     Running   0          7s    10.244.0.11   minikube   <none>           <none>
    flashsale-rs-lhf4p   1/1     Running   0          89s   10.244.0.6    minikube   <none>           <none>
    flashsale-rs-nczxz   1/1     Running   0          15s   10.244.0.9    minikube   <none>           <none>
    flashsale-rs-nglpf   1/1     Running   0          15s   10.244.0.10   minikube   <none>           <none>
    flashsale-rs-qz88x   1/1     Running   0          89s   10.244.0.7    minikube   <none>           <none>

Load distribution: requests to the Service were served by different Pods. Four responses were captured before the test was stopped:

    {"item":"Smartphone","served_by_pod":"flashsale-rs-2bbtq","status":"success","time":"18:10:07","user":"user771"}
    {"item":"Headphones","served_by_pod":"flashsale-rs-qz88x","status":"success","time":"18:10:07","user":"user778"}
    {"item":"Smartphone","served_by_pod":"flashsale-rs-nczxz","status":"success","time":"18:10:07","user":"user206"}
    {"item":"Headphones","served_by_pod":"flashsale-rs-2bbtq","status":"success","time":"18:10:07","user":"user396"}

## Key Observations
- **Scaling:** a ReplicaSet keeps the desired number of identical Pods running. Changing `replicas` from 3 to 5 simply creates two more clones.
- **Resiliency:** when a Pod was deleted, the ReplicaSet created a replacement within a second, so the Service always had healthy Pods behind it.
- **Load distribution:** the Service spreads requests across Pods. The `served_by_pod` field shows three different Pods answering four requests.
- **Efficiency:** replicas can be added for a traffic spike (like a flash sale) and removed afterwards, instead of over-provisioning.

## Notes
- The brief's Dockerfile copies `ex3-flash-sale.py` and later steps use the name `flask-app-rs`. I saved the app as `app.py` (matching gunicorn's `app:app`) and used `flashsale-rs` and `flashsale:1.0` consistently, as in the YAML.
- The image was loaded into Minikube with `minikube image load` instead of being pushed to Docker Hub, because `minikube docker-env` does not work with the containerd runtime on Windows.
- A bare ReplicaSet does not do rolling updates. A Deployment, which manages ReplicaSets, is the usual choice for that.

## Files
- `app.py`: Flask application.
- `Dockerfile`: Image definition (gunicorn on port 5000).
- `flashsale-replicaset.yaml`: ReplicaSet and ClusterIP Service.

## Cleanup

    kubectl delete -f flashsale-replicaset.yaml
