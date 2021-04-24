FROM python:3.8

# set uids and gids env variables
ENV usr dockeruser
ENV grp dockeruser

# prepare home directory
RUN mkdir -p /home/$usr/
RUN groupadd -g 1000 $grp && \
    useradd -r -u 1000 -g $grp -d /home/$usr/ $usr
RUN chown $usr:$grp /home/$usr/
# from now we work not under root

# EXPOSE 8001

# copy app dir, install dependencies and run entry_point bash script
USER $usr
RUN mkdir -p /home/$usr/workdir
COPY service /home/$usr/workdir

# USER root
# RUN chmod +x /home/$usr/workdir/configs/entry_point.sh

USER $usr
RUN pip3 install --user -r /home/$usr/workdir/requirements.txt
ENTRYPOINT /home/dockeruser/.local/bin/uwsgi /home/$usr/workdir/uwsgi.ini
