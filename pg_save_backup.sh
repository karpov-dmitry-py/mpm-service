#!/bin/bash

/usr/local/bin/docker-compose exec pg pg_dump -U srvc_user -F p srvc_db > /tmp/srvc_pg_dump.sql