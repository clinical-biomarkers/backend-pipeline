#srv="prd"
#srv="beta"
#srv="tst"
srv="dev"

sudo systemctl stop docker-bmkb-api-$srv.service
python3 create-api-container.py -s $srv
sudo systemctl start docker-bmkb-api-$srv.service


docker volume prune -a -f 
docker buildx prune -a -f
docker builder prune -a -f




