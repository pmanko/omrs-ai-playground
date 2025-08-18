ARG PLATFORM_VERSION=latest

FROM jembi/platform:$PLATFORM_VERSION
ADD . /implementation

ENV DOCKER_CONTEXT=default

ADD ./utils /instant/utils


RUN chmod +x /implementation/scripts/cmd/override-configs/override-configs
RUN /implementation/scripts/cmd/override-configs/override-configs

