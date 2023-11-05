FROM --platform=$BUILDPLATFORM debian:bullseye-slim as docker-client

ARG ARG_DOCKER_CLIENT_VERSION=20.10.17
ARG ARG_DOCKER_API_VERSION=1.41
ARG ARG_DOCKER_ARCH=

ENV DOCKER_CLIENT_VERSION=${ARG_DOCKER_CLIENT_VERSION}
ENV DOCKER_API_VERSION=${ARG_DOCKER_API_VERSION}}

ARG TARGETPLATFORM
RUN apt-get update \
    && apt-get install -y curl \
    && if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
    ARG_DOCKER_ARCH=aarch64 ; \
    elif [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
    ARG_DOCKER_ARCH=x86_64 ; \
    fi \
    && curl -Lo docker-${DOCKER_CLIENT_VERSION}.tgz https://download.docker.com/linux/static/stable/${ARG_DOCKER_ARCH}/docker-${DOCKER_CLIENT_VERSION}.tgz \
    && tar xzvf docker-${DOCKER_CLIENT_VERSION}.tgz \
    && chmod +x docker/*

FROM --platform=$BUILDPLATFORM python:3.10.8-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    GROUPNAME=user \
    USERNAME=user \
    PASSWORD=user \
    APP_DIR=/app
ARG GIT_VERSION=2.39.1 \
    TARGETPLATFORM

COPY --from=docker-client docker/* /usr/bin/

RUN apt-get update -y \
    && apt-get install -yq \
    unzip \
    wget \
    curl \
    sudo \
    locales \
    gcc \
    libssl-dev \
    libcurl4-openssl-dev \
    libmagic1 \
    locales \
    openssh-client \
    g++ \
    ca-certificates \
    vim \
    gnupg2 \
    make \
    procps \
    libexpat1-dev \
    gettext \
    libz-dev \
    jq \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && sed -i -e 's/# \(ja_JP.UTF-8\)/\1/' /etc/locale.gen && locale-gen \
    && python -m pip install --upgrade pip \
    && python -m pip install pipenv lefthook \
    && cd /usr/local/src \
    && wget https://github.com/git/git/archive/refs/tags/v${GIT_VERSION}.tar.gz \
    && tar -xzf v${GIT_VERSION}.tar.gz \
    && cd git-${GIT_VERSION} \
    && make prefix=/usr/local all -j "$(nproc)" \
    && make prefix=/usr/local install \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "/tmp/awscliv2.zip"; \
    elif [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"; \
    fi; \
    cd /tmp/; \
    unzip awscliv2.zip; \
    ./aws/install; \
    rm -rf awscliv2.zip ./aws; \
    aws --version;

ARG DOCKER_UID=1100 \
    DOCKER_GID=1100

RUN groupadd --system --gid $DOCKER_GID ${GROUPNAME} \
    && useradd --system --gid $DOCKER_GID -G sudo -m --uid $DOCKER_UID ${USERNAME} \
    && echo $USERNAME:$PASSWORD | chpasswd \
    && echo "$USERNAME   ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && mkdir -p ${APP_DIR}/.venv /home/user/.vscode-server/extensions \
    && chown -R ${USERNAME}:${GROUPNAME} /home/${USERNAME} ${APP_DIR} /home/user/.vscode-server/extensions \
    && echo 'pcm.!default {\n type hw\n card 0\n}\n\nctl.!default {\n type hw\n card 0\n}' > /home/user/.asoundrc \
    && localedef -f UTF-8 -i ja_JP ja_JP.utf8

USER ${USERNAME}

ENV PIPENV_VENV_IN_PROJECT=1 \
    LANG=ja_JP.UTF-8 \
    LC_CTYPE=ja_JP.UTF-8

WORKDIR /app
CMD [ "bash" ]
