server {

    #listen [::]:443;
    listen 443 ssl;
    server_name marketplace-master.ru;
    ssl_certificate /etc/ssl/marketplace-master.ru.crt;
    ssl_certificate_key /etc/ssl/marketplace-master.ru.key;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    keepalive_timeout 70;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_stapling on;
    ssl_trusted_certificate /etc/ssl/ca.crt;
    resolver 8.8.8.8;

    # max upload size
    client_max_body_size 75M;

    location / {
        proxy_pass http://localhost:8001;
        include    proxy_params;
    }

    location = /favicon.ico {
        access_log      off;
        log_not_found   off;
    }
}
