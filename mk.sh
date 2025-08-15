./build-custom-images.sh
./build-image.sh

#./instant project up --env-file .env -d
#./instant project down --env-file .env
#./instant project destroy --env-file .env
#./instant project init --env-file .env

./instant package destroy -n database-mysql
./instant package init -n database-mysql -d

./instant package destroy -n emr-openmrs
./instant package init -n emr-openmrs -d
# ./instant package down -n emr-openmrs
# ./instant package up -n emr-openmrs -d

# ./instant package destroy -n redis
# ./instant package init -n redis -d

# ./instant package destroy -n omrs-appo-service
# ./instant package init -n omrs-appo-service -d

# ./instant package destroy -n reverse-proxy-nginx
# ./instant package init -n reverse-proxy-nginx




