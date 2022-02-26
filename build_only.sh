 #!/bin/bash

echo ">>>> cleaning up project dir from local dev files  ..."
sudo rm -f ./service/scheduler_lock.file
sudo cat /dev/null > ./service/cron.log

echo ">>>> building docker image ..."
sudo /usr/bin/docker build -t 'mpm_service_app' --no-cache /home/dkarpov/projects/self/mpm-service/
