FROM docker.io/library/ubuntu:noble

ARG DEBIAN_FRONTEND="noninteractive"

# install baseline tooling
RUN apt-get update \
  && apt-get install -y \
    bash-completion \
    build-essential \
    cmake \
    libcairo2-dev \
    nano \
    openssh-client \
    python-is-python3 \
    python3-poetry \
    sudo \
  && rm -rf /var/lib/apt/lists/*

# setup project workspace
ARG WORKSPACE=/opt/work
RUN mkdir -p ${WORKSPACE}
WORKDIR ${WORKSPACE}

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

CMD ["/bin/bash"]
