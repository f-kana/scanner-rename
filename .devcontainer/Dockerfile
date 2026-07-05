FROM mcr.microsoft.com/devcontainers/python:3.13

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Install Google Cloud CLI and Byobu
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
        > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && CLOUDSDK_SKIP_PY_COMPILATION=1 apt-get install -y --no-install-recommends \
        google-cloud-cli \
        byobu \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Zellij
RUN ARCH=$(uname -m) \
    && ZELLIJ_VERSION=$(curl -fsSL https://api.github.com/repos/zellij-org/zellij/releases/latest | grep '"tag_name"' | sed 's/.*"v\(.*\)".*/\1/') \
    && curl -fsSL "https://github.com/zellij-org/zellij/releases/download/v${ZELLIJ_VERSION}/zellij-${ARCH}-unknown-linux-musl.tar.gz" \
        | tar xz -C /usr/local/bin \
    && zellij --version

# Install Herdr (AI agent multiplexer)
RUN ARCH=$(uname -m) \
    && HERDR_VERSION=$(curl -fsSL https://api.github.com/repos/ogulcancelik/herdr/releases/latest | grep '"tag_name"' | sed 's/.*"v\(.*\)".*/\1/') \
    && curl -fsSL "https://github.com/ogulcancelik/herdr/releases/download/v${HERDR_VERSION}/herdr-linux-${ARCH}" \
        -o /usr/local/bin/herdr \
    && chmod +x /usr/local/bin/herdr \
    && herdr --version
