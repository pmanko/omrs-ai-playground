./build-custom-images.sh
./build-image.sh

#./instant project up --env-file .env -d
#./instant project down --env-file .env
#./instant project destroy --env-file .env
#./instant project init --env-file .env

sudo ./instant package destroy -n database-mysql
sudo ./instant package init -n database-mysql -d

sudo ./instant package destroy -n emr-openmrs
sudo ./instant package init -n emr-openmrs -d

sudo ./instant package destroy -n redis
sudo ./instant package init -n redis -d

sudo ./instant package destroy -n omrs-appo-service
sudo ./instant package init -n omrs-appo-service -d




