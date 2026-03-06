#docker images -f dangling=true
docker images -f dangling=true  | awk '{print "docker image rm -f " $3}'



