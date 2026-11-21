# Based on Evidence's own self-host image (cli/Dockerfile in
# evidence-dev/evidence): the pinned CLI binary, run as `evidence serve`.
FROM debian:bookworm-slim AS install
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*
ARG EVIDENCE_VERSION=0.12.2
ARG TARGETARCH
RUN set -e; \
  case "$TARGETARCH" in \
    amd64) target=linux-x64 ;; \
    arm64) target=linux-arm64 ;; \
    *) echo "unsupported arch: $TARGETARCH" && exit 1 ;; \
  esac; \
  curl -fsSL "https://gaamozau3jchzs3r.public.blob.vercel-storage.com/cli/v${EVIDENCE_VERSION}/evidence-${target}" \
    -o /usr/local/bin/evidence; \
  chmod +x /usr/local/bin/evidence

FROM debian:bookworm-slim
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*
COPY --from=install /usr/local/bin/evidence /usr/local/bin/evidence
RUN useradd --create-home --uid 10001 evidence
COPY --chown=evidence:evidence project /project
USER evidence
WORKDIR /project
EXPOSE 3000
# Serving on a non-loopback host requires basic auth: see compose.yaml.
CMD ["evidence", "serve", "--host", "0.0.0.0", "--no-open", "--port", "3000"]
