FROM python:3.12-bullseye

WORKDIR /app
COPY main.py requirements.txt entrypoint.sh latency-test.sh /app/
RUN pip install -r requirements.txt

RUN chmod +x entrypoint.sh && \
    chmod +x latency-test.sh && \
    git clone https://github.com/microsoft/lagscope.git && \
    cd lagscope && \
    apt update -y && \
    apt install -y cmake build-essential && \
    ./do-cmake.sh build

# don't buffer python stdout
ENV PYTHONUNBUFFERED=1

# lagscope/build/lagscope -r -p6789

ENTRYPOINT [ "./entrypoint.sh" ]
