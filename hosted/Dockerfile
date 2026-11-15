FROM eclipse-temurin:21-jdk-jammy AS java
FROM python:3.13-slim-bookworm
COPY --from=java /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="/opt/java/openjdk/bin:${PATH}"
ENV CSE_SYSML_CACHE=/opt/cse-parser CSE_JOB_ROOT=/work/jobs
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/cse
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY hosted/requirements.lock hosted/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r hosted/requirements.lock
COPY plugin.json LICENSE ./
COPY scripts ./scripts
COPY verifier ./verifier
COPY tools/sysml ./tools/sysml
COPY skills ./skills
COPY assets ./assets
COPY docs ./docs
COPY hosted/*.py ./hosted/
RUN python scripts/install_sysml_parser.py \
    && rm /opt/cse-parser/jupyter-sysml-kernel-0.52.0.zip \
    && groupadd -g 10001 cse && useradd -u 10001 -g cse --no-create-home cse \
    && mkdir -p /work/jobs && chown -R cse:cse /work/jobs /opt/cse-parser
USER 10001:10001
EXPOSE 8080
CMD ["python", "-B", "-m", "hosted.server"]
