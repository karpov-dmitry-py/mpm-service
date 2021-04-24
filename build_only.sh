 #!/bin/bash

echo ">>>> building docker image ..."
sudo /usr/bin/docker build -t 'mpm_service_app' /home/dkarpov/projects/self/mpm-service/
