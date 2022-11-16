FROM python:3

WORKDIR /home/app

ADD cburnfs /home/app/cburnfs
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r cburnfs/requirements.txt
