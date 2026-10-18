# Exercise 10 - Minikube Multi-Node Multi-App Deployment

## Objective
Run two Flask apps (product catalog, shopping cart) on a 3-node Minikube cluster, spread across nodes with pod anti-affinity, and expose each with a NodePort service.

## Files
- `product_catalog.py`, `shopping_cart.py` - the apps, verbatim from the exercise
- `Dockerfile.product`, `Dockerfile.shopping` - images for each app
- `product_catalog_deployment.yaml`, `shopping_cart_deployment.yaml` - 2 and 3 replicas, required anti-affinity on `kubernetes.io/hostname`
- `product_catalog_service.yaml`, `shopping_cart_service.yaml` - NodePort services
- `cart_item.json` - request body for the POST test

## Steps and results

1. Created the cluster and enabled the registry addon:

        minikube start --nodes 3 -p devops-multinode --force
        minikube -p devops-multinode addons enable registry
        kubectl get nodes

   All three nodes (`devops-multinode`, `-m02`, `-m03`) were `Ready`.

2. Built both images and loaded them into the cluster:

        docker build -t product-catalog:latest -f Dockerfile.product .
        docker build -t shopping-cart:latest -f Dockerfile.shopping .
        minikube -p devops-multinode image load product-catalog:latest
        minikube -p devops-multinode image load shopping-cart:latest

   `crictl images` on each of the three nodes listed both images.

3. Applied the four manifests and waited for the rollouts. Result of `kubectl get pods -o wide`:

        NAME                             READY   STATUS    NODE
        product-catalog-7cb85d4f-68nh2   1/1     Running   devops-multinode-m03
        product-catalog-7cb85d4f-9wj7c   1/1     Running   devops-multinode-m02
        shopping-cart-6858b5f797-dpdpd   1/1     Running   devops-multinode-m02
        shopping-cart-6858b5f797-kvs8v   1/1     Running   devops-multinode-m03
        shopping-cart-6858b5f797-l52s6   1/1     Running   devops-multinode

   Anti-affinity worked: no two pods of the same app share a node.

        NAME                      TYPE       CLUSTER-IP       PORT(S)
        product-catalog-service   NodePort   10.106.111.86    80:30684/TCP
        shopping-cart-service     NodePort   10.111.135.250   80:32252/TCP

4. Tested through `minikube service --url` tunnels (`$pc` = product catalog, `$sc` = shopping cart):

        curl.exe -s "$pc/products"
        [{"id":1,"name":"Laptop","price":1200},{"id":2,"name":"Phone","price":800},{"id":3,"name":"Headphones","price":150}]

        curl.exe -s "$sc/cart"
        []

        curl.exe -s -X POST -H "Content-Type: application/json" -d "@cart_item.json" "$sc/cart"
        [{"id":1,"name":"Laptop","quantity":1}]

        curl.exe -s "$sc/cart"
        []

   The last `GET /cart` is empty because the cart is an in-memory list inside each pod and the service load-balances across 3 pods. Nine more GETs returned the Laptop on only 2 of them, which are the calls that reached the pod that received the POST. This is a property of the exercise's app (no shared storage), not a cluster fault.

## Differences from the exercise instructions
- **Namespace:** `shopping_cart_deployment.yaml` uses `default` instead of `devops-exercise`, which does not exist in the cluster and would make `kubectl apply` fail. The other three manifests already used `default`.
- **Image check on nodes:** the nodes run containerd, so `minikube ssh -- docker images` fails with "Cannot connect to the Docker daemon". I ran it anyway, then used `sudo crictl images` on each node.
- **Old cluster:** the earlier `minikube` profile was deleted first to free memory for three nodes, and the Jenkins container was stopped.
- **Registry addon:** enabled as instructed but not used; images were loaded with `minikube image load` and the deployments use `imagePullPolicy: Never`.
- **Service access:** with the Docker driver on Windows, node IPs are not reachable from the host, so each service was opened with `minikube service --url` in its own PowerShell window and the printed `127.0.0.1` URLs were used for curl.
- **POST test:** the JSON body is sent from `cart_item.json` (`-d "@cart_item.json"`) because PowerShell mangles inline JSON quotes.
- **Warnings seen and ignored:** `--force` skips validation, a failed connection to `registry.k8s.io` from `-m02`, and a kubectl 1.34.1 / cluster 1.37.0 version skew.

## Cleanup

    minikube delete -p devops-multinode
