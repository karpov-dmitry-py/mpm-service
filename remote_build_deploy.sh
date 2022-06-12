 #!/bin/bash

echo ">>>> building docker image ..."
sudo /usr/bin/docker build --rm -t 'mpm_service_app' /home/dockeruser/service/code/mpm-service

#echo ">>>> stopping and removing existing docker containers ..."
#/bin/bash ./service_down.sh

echo ">>>> creating and starting new docker containers ..."
/bin/bash ./service_up.sh



