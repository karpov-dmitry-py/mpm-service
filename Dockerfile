FROM python:3.8

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
# ENV LANGUAGE en_US.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING utf-8

RUN apt-get update && \
    apt-get install -y apt-transport-https && \
    apt-get install -y cron

# set uids and gids env variables
ENV usr dockeruser
ENV grp dockeruser

# prepare home directory
RUN mkdir -p /home/$usr/
RUN groupadd -g 1000 $grp && useradd -r -u 1000 -g $grp -d /home/$usr/ $usr
RUN chown $usr:$grp /home/$usr/
# from now we work not under root

# EXPOSE 8001

# copy app dir, install dependencies and run entry_point bash script
USER $usr
RUN mkdir -p /home/$usr/workdir
COPY service /home/$usr/workdir

# USER root
# RUN chmod +x /home/$usr/workdir/configs/entry_point.sh

# CRON
# RUN mkdir /etc/cron.d
USER root
RUN chown $usr:$grp /home/$usr/workdir/tasks/
RUN echo $usr > /etc/cron.allow && echo "" >> /etc/cron.allow
RUN chmod gu+rw /var/run && chmod gu+s /usr/sbin/cron
RUN chmod -R 666 /etc/cron.d
RUN chmod -R 666 /home/$usr/workdir/cron.log

USER $usr
RUN pip install --user -r /home/$usr/workdir/requirements.txt
# CMD cron -L 15
CMD tail -f /home/$usr/workdir/cron.log
ENTRYPOINT /home/dockeruser/.local/bin/uwsgi /home/$usr/workdir/uwsgi.ini
