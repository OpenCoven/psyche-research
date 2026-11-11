ARG PG_MAJOR=16
FROM postgres:${PG_MAJOR}-trixie

# Dependencies are installed only in the disposable CI image. Runtime has no network.
RUN apt-get update
RUN apt-get install -y --no-install-recommends python3 python3-venv git
RUN python3 -m venv /opt/role-venv
COPY requirements.txt /tmp/role-requirements.txt
RUN /opt/role-venv/bin/python -m pip install --require-hashes -r /tmp/role-requirements.txt
RUN git config --system --add safe.directory /source

# The exact checkout is mounted read-only; git archive needs no credentials or writes.
USER postgres
WORKDIR /source
ENTRYPOINT ["/opt/role-venv/bin/python", "-I", "-B"]
