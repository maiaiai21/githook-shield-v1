FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html

RUN mkdir -p /usr/share/nginx/html/evaluation

COPY dashboard/index.html /usr/share/nginx/html/dashboard/index.html
COPY dashboard/index.html /usr/share/nginx/html/index.html
COPY dashboard/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
