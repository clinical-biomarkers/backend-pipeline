sudo systemctl stop docker-bmkb-api.service
python3 create-api-container.py 
sudo systemctl start docker-bmkb-api.service


#docker volume prune -a -f 
#docker buildx prune -a -f
#docker builder prune -a -f




