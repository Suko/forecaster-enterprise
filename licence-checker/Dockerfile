FROM curlimages/curl:latest

USER root
RUN apk add --no-cache jq coreutils util-linux dos2unix docker-cli

WORKDIR /app
COPY licence-checker.sh .
RUN dos2unix licence-checker.sh && chmod +x licence-checker.sh

CMD ["./licence-checker.sh"]