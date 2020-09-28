FROM python:3.8-buster as build

COPY ./requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.8-slim

#  copy over cached python wheels and build from wheels
COPY --from=build /root/.cache /root/.cache
COPY ./requirements.txt ./

RUN pip install --upgrade pip && pip install -r requirements.txt
RUN apt-get update && apt-get install -y libpq-dev && apt-get clean

COPY *.py ./

CMD ["python", "worm.py"]