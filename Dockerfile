FROM python:2.7

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "py/prioritize.py" ]

# BUILD docker build -t fast-env .
# RUN docker run -it -v $PWD:/usr/src/app fast-env bash