# xhost +local:docker
# docker run -it --device=/dev/dri:/dev/dri -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix pycgns
FROM python:3.6

RUN apt-get update && apt-get install -y \
            python3-pip libhdf5-dev build-essential \
            python3-pyqt5 x11-apps qt5-default cgns-convert \
            libopenmpi-dev

RUN mkdir app
COPY setup.py /app/setup.py
COPY setup_userConfig.py /app/setup_userConfig.py
COPY CGNS /app/CGNS
COPY lib /app/lib
COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install -r requirements.txt
RUN pip3 install QtPy PyQt5 PyQt5-sip
RUN python3 setup.py build
RUN python3 setup.py install

COPY demo /app/demo

# tests
WORKDIR /tmp
RUN python3 -c 'import CGNS.APP.test;CGNS.APP.test.run()'
RUN python3 -c 'import CGNS.NAV.test;CGNS.NAV.test.run()'
RUN python3 -c 'import CGNS.PAT.test;CGNS.PAT.test.run()'
RUN python3 -c 'import CGNS.VAL.test;CGNS.VAL.test.run()'

# IHM
ENTRYPOINT ["python3", "/app/build/scripts-3.6/cg_look"]
