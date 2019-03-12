ARG PY=3
FROM python:$PY as builder
RUN pip install tox pytest flake8
ADD .build /py
WORKDIR /py
ENV PATH=$PATH:/root/.local/bin
RUN make tox install test-install uninstall
RUN make clean && rm -rf .tox

FROM python:$PY
COPY --from=builder /py /py
RUN  make -C /py install
