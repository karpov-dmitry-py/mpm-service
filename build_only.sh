 #!/bin/bash

echo ">>>> building docker image ..."
sudo /usr/bin/docker build -t 'mpm_service_app' --no-cache /home/dkarpov/projects/self/mpm-service/
