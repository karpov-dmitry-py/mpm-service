 #!/bin/bash

/bin/bash ./build_only.sh

echo ">>>> saving docker image to a tar archive ..."
/usr/bin/docker image save -o mpm_service.tar mpm_service_app

echo ">>>> copying tar archive to remote host via ssh ..."
/usr/bin/scp mpm_service.tar dockeruser@185.46.8.53:/home/dockeruser/service/deploy

echo ">>>> ssh-ing to remote host and running deploy on it ..."
/bin/bash ./ssh_and_deploy.sh

echo ">>>> removing *.tar files on host ..."
rm *.tar

echo ">>>> done!"