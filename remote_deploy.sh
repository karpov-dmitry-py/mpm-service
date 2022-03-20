 #!/bin/bash

echo ">>>> loading docker image from a tar archive ..."
/usr/bin/docker image load -i mpm_service.tar

echo ">>>> stopping and removing existing docker containers ..."
/bin/bash ./service_down.sh

echo ">>>> creating and starting new docker containers ..."
/bin/bash ./service_up.sh



