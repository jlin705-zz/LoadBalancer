# LoadBalancer
## Start Server:
```
$ while true; do nc -l LB_port < response.html;done
```
## Request from Client:
```
$ echo -n "GET / HTTP/1.0\r\n\r\n" | nc localhost LB_port
```
## Start Load Balancer:
```
python LoadBalancer.py
```
