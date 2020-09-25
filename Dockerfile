FROM python:2.7

WORKDIR /home/fast/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN echo "PS1='\[\033[1;36m\]FAST \[\033[1;34m\]\w\[\033[0;35m\] \[\033[1;36m\]# \[\033[0m\]'" >> ~root/.bashrc

CMD [ "python", "py/prioritize.py" ]

# BUILD docker build -t fast-env .
# RUN docker run -it --rm -v $PWD:/home/fast/ fast-env bash