FROM defects4j:2.0.0

WORKDIR /home/fast/

RUN apt-get -y update && \
    apt-get install -y python2 && \
    curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py && \
    python2 get-pip.py && \
    apt-get install -y ant
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN echo "PS1='\[\033[1;36m\]FAST \[\033[1;34m\]\w\[\033[0;35m\] \[\033[1;36m\]# \[\033[0m\]'" >> ~root/.bashrc

CMD [ "python", "py/prioritize.py" ]

# BUILD docker build -t fast-env .
# RUN docker run -it --rm -v $PWD:/home/fast/ -v $PWD/defects_folder/defects4j.build.xml:/defects4j/framework/projects/defects4j.build.xml fast-env:d4j bash 