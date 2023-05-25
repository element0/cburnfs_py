FROM alpine:latest

WORKDIR /home/laydbug
ADD cburnfs /home/laydbug/cburnfs

RUN apk update && apk add python3 \
&& apk add py3-pip \
&& pip install --upgrade pip \
&& pip install -r cburnfs/requirements.txt \
&& CBURNFS_PATH=$(python3 -c 'import site; print(site.USER_SITE)')\
&& echo CBURNFS_PATH=${CBURNFS_PATH} \
&& mkdir -p ${CBURNFS_PATH} \
&& ls \
&& mv cburnfs ${CBURNFS_PATH}/cburnfs \
&& mv ${CBURNFS_PATH}/cburnfs/blackstrap.py ${CBURNFS_PATH}/blackstrap.py


# ls required to make mv work - a docker bug?
# blackstrap must be at same level in order to work
