# images
#docker image ls
#docker image ls -f dangling=true
docker volume prune -a

#volumes
#docker volume ls
#docker volume ls -f dangling=true 
docker volume prune -a


# build caches
docker buildx prune -a
docker builder prune -a



