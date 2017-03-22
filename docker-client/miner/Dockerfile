FROM ubuntu
RUN apt-get update
RUN apt-get install -y python3 
RUN apt-get install -y python3-pip
RUN apt-get install -y git
RUN pip3 install websockets
RUN pip3 install asyncio
RUN pip3 install pycrypto
RUN git clone https://github.com/csgames/cscoins.git
WORKDIR cscoins/src/minerclient/
ENTRYPOINT python3 main.py
