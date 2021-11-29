FROM python:3.9-slim
WORKDIR /src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ./src /src
EXPOSE 5000
ENV SERVER='0.0.0.0'
CMD python server.py