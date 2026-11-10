FROM httpd:2.4

RUN sed -i \
    -e 's/^#LoadModule proxy_module/LoadModule proxy_module/' \
    -e 's/^#LoadModule proxy_http_module/LoadModule proxy_http_module/' \
    /usr/local/apache2/conf/httpd.conf

COPY conf/task-proxy.conf \
    /usr/local/apache2/conf/extra/task-proxy.conf

RUN echo "Include conf/extra/task-proxy.conf" \
    >> /usr/local/apache2/conf/httpd.conf

COPY html/ /usr/local/apache2/htdocs/

EXPOSE 80

CMD ["httpd-foreground"]
