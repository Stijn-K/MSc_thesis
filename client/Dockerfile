FROM python:3.9-slim
WORKDIR /src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ./src /src
ENV SERVER='server'
ENV CHROMEDRIVER=''
CMD python client.py
