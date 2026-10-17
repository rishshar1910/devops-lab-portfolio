# Exercise 4: Docker Networking with Multiple Containers

## Objective
Understand Docker networking by running a three-container application (Flask API, MySQL, Redis) on a user-defined bridge network, and demonstrate container-to-container DNS and host-to-container port publishing.

## Architecture

    Host (localhost:5001)
            |
            v
    +-----------------+
    |  flask  :5001   |
    +--------+--------+
             |
        my-bridge-net
      +------+-------+
      |              |
    +-------+     +-------+
    | mysql |     | redis |
    +-------+     +-------+

- Host to Flask uses the published port (`-p 5001:5001`).
- Flask to MySQL and Flask to Redis use the internal Docker network and container names. Ports 3306 and 6379 are not published.

## Prerequisites
- Docker Desktop

## Implementation
1. Created a user-defined bridge network, `my-bridge-net`.
2. Wrote a small Flask API (`app.py`) with a `/about` endpoint, a `requirements.txt` and a `Dockerfile`, and built the image `flask-api`.
3. Started MySQL and Redis on the network from the official images.
4. Started Flask on the same network and published port 5001 to the host.
5. Verified the API from the host, and DNS resolution and ping from inside the Flask container.
6. Verified Redis (`PONG`) and MySQL (`SHOW DATABASES`).

## Commands Used

    docker network create --driver bridge my-bridge-net
    docker network ls
    docker network inspect my-bridge-net
    docker build -t flask-api .
    docker run -d --name mysql --network my-bridge-net -e MYSQL_ROOT_PASSWORD=rootpass -e MYSQL_DATABASE=devopsdb mysql:latest
    docker run -d --name redis --network my-bridge-net redis:latest
    docker run -d --name flask --network my-bridge-net -p 5001:5001 flask-api
    docker ps
    docker port flask
    curl.exe http://localhost:5001/about
    docker exec flask bash -c "apt-get update -qq && apt-get install -y -qq iputils-ping"
    docker exec flask ping -c 3 mysql
    docker exec flask ping -c 3 redis
    docker exec flask getent hosts mysql
    docker exec flask getent hosts redis
    docker exec redis redis-cli ping
    docker exec mysql mysql -uroot -prootpass -e "SHOW DATABASES;"

## Output

Network created:

    $ docker network ls
    NETWORK ID     NAME            DRIVER    SCOPE
    2dacb6ad33a3   bridge          bridge    local
    fa9b33fc2723   host            host      local
    4b0d30ddcfc2   minikube        bridge    local
    c11e74235539   my-bridge-net   bridge    local
    80d30e72e9f3   none            null      local

Network subnet and gateway (from `docker network inspect my-bridge-net`):

    "Subnet": "172.18.0.0/16",
    "Gateway": "172.18.0.1"

All three containers attached to the network:

    "Containers": {
        redis  -> IPv4Address 172.18.0.3/16
        mysql  -> IPv4Address 172.18.0.2/16
        flask  -> IPv4Address 172.18.0.4/16
    }

Published port and API test from the host:

    $ docker port flask
    5001/tcp -> 0.0.0.0:5001
    5001/tcp -> [::]:5001

    $ curl.exe http://localhost:5001/about
    {"description":"This is a simple REST API built with Flask.","name":"Simple REST API","version":"1.0"}

Name-based connectivity from inside the Flask container:

    $ docker exec flask ping -c 3 mysql
    PING mysql (172.18.0.2) 56(84) bytes of data.
    64 bytes from mysql.my-bridge-net (172.18.0.2): icmp_seq=1 ttl=64 time=0.500 ms
    64 bytes from mysql.my-bridge-net (172.18.0.2): icmp_seq=2 ttl=64 time=0.087 ms
    64 bytes from mysql.my-bridge-net (172.18.0.2): icmp_seq=3 ttl=64 time=0.101 ms
    3 packets transmitted, 3 received, 0% packet loss

    $ docker exec flask ping -c 3 redis
    PING redis (172.18.0.3) 56(84) bytes of data.
    64 bytes from redis.my-bridge-net (172.18.0.3): icmp_seq=1 ttl=64 time=0.369 ms
    64 bytes from redis.my-bridge-net (172.18.0.3): icmp_seq=2 ttl=64 time=0.100 ms
    64 bytes from redis.my-bridge-net (172.18.0.3): icmp_seq=3 ttl=64 time=0.075 ms
    3 packets transmitted, 3 received, 0% packet loss

    $ docker exec flask getent hosts mysql
    172.18.0.2      mysql
    $ docker exec flask getent hosts redis
    172.18.0.3      redis

Service checks:

    $ docker exec redis redis-cli ping
    PONG

    $ docker exec mysql mysql -uroot -prootpass -e "SHOW DATABASES;"
    Database
    devopsdb
    information_schema
    mysql
    performance_schema
    sys

## Key Learnings
- A user-defined bridge network gives containers built-in DNS, so they reach each other by name instead of hard-coded IP addresses (which can change).
- Port publishing (`-p HOST:CONTAINER`) is only for access from outside the network. Flask does not need MySQL's or Redis's ports published to talk to them.
- Bridge networking gives each container its own network namespace; host networking would share the host's network stack.
- A Flask app inside a container must listen on `0.0.0.0`, not the default `127.0.0.1`, or published ports cannot reach it.

## Notes
- The brief's `app.py` used `app.run(debug=True, port=5001)`, which listens only on the container's loopback. I changed it to `host='0.0.0.0'`.
- I pinned `Werkzeug==2.0.3` alongside `Flask==2.0.1`, since Flask 2.0.1 is incompatible with newer Werkzeug releases.
- MySQL needs a root password to start, so I set `MYSQL_ROOT_PASSWORD` and `MYSQL_DATABASE`. `rootpass` is a throwaway lab value, not a real credential.
- I used `--network`, the current spelling of the older `--net` flag.
- `ping` is not in the slim Python image, so it was installed inside the running container for the test.

## Files
- `app.py`: Flask API.
- `requirements.txt`: Pinned Python dependencies.
- `Dockerfile`: Image definition for the Flask app.

## Cleanup

    docker stop mysql redis flask
    docker rm mysql redis flask
    docker network rm my-bridge-net
