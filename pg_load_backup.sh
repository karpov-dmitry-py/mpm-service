#!/bin/bash

/usr/local/bin/docker-compose exec pg pg_restore -U srvc_user -d srvc_db -F t /tmp/srvc_pg_dump.tar
