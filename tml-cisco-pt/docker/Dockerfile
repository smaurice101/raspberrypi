# Iot Solution ARM32 docker
FROM python:3.9-slim

# The service name for TML solution
# ARG service_name


# Transactional Machine Learning (TML) with Kafka/Java/Python for ARM 32
# install java
ARG CHIP
ENV CHIP=${CHIP}
################################# DEFINE RUNTYPE: 0=Production using Kafka Cloud, 1=Development using local data file: cisco_network_data.txt
#####  pass in docker build and run (--env RUNTYPE=0 to override)

ENV RUNTYPE=1
RUN export RUNTYPE

ENV VIPERVIZPORT=9000
RUN export VIPERVIZPORT

ENV BROKERHOSTPORT=127.0.0.1:9092
RUN export BROKERHOSTPORT

ENV CLOUDUSERNAME=""
RUN export CLOUDUSERNAME
ENV CLOUDPASSWORD=""
RUN export CLOUDPASSWORD

ENV HACKEDHOSTS="5.11-i,5.16-i,6.17-i"
RUN export HACKEDHOSTS

ENV KAFKAPRODUCETOPIC="cisco-network-mainstream"
RUN export KAFKAPRODUCETOPIC

#ARG CHIP="ARM32"
#CHIP="ARM64"
#CHIP="AMD64"
#CHIP="MAC"
#CHIP="WINDOWS"

#echo "Updating package index files"
RUN apt update || true
RUN apt install -y wget
RUN apt-get -y install git
RUN apt-get -y install unzip
RUN apt-get -y install vim
RUN apt-get -y install nano


RUN echo "Downloading and Installing TML technologies "
RUN echo "Downloading and Installing VIPER"
RUN mkdir Viper-produce
RUN chmod -R +x Viper-produce

RUN mkdir Viper-preprocess
RUN chmod -R +x Viper-preprocess

RUN mkdir Kafka
RUN chmod -R +x Kafka

WORKDIR Kafka

RUN echo "Downloading and Installing KAFKA"

RUN wget -O kafka_2.13-3.0.0.tgz https://archive.apache.org/dist/kafka/3.0.0/kafka_2.13-3.0.0.tgz
RUN chmod +x kafka_2.13-3.0.0.tgz

RUN tar xzf kafka_2.13-3.0.0.tgz

RUN export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"
RUN export PWD=`pwd`
RUN export CHIP="$CHIP"

RUN export PATH="$PATH:$PWD/Kafka/kafka_2.13-3.0.0/bin"

RUN rm -rf kafka_2.13-3.0.0.tgz
WORKDIR /
RUN chmod -R +x Kafka

RUN echo "Install TMUX"
RUN apt -y install tmux
RUN mkdir tmux

RUN echo "Install Mariadb"
RUN apt -y install mariadb-server

# sudo mysql_secure_installation
# RUN: sudo mysql -u root
# Execute: SET PASSWORD FOR 'root'@'localhost' = PASSWORD('raspberry'); 
# GRANT ALL PRIVILEGES on *.* to 'root'@'localhost' IDENTIFIED BY 'raspberry'; 
# FLUSH PRIVILEGES;

WORKDIR /

RUN echo "Installing Java"
RUN apt -y install default-jdk || true

RUN echo "PIP Install TML core packages"
RUN pip install requests
RUN pip install nest_asyncio
RUN pip install joblib
RUN pip install asyncio

############################################################### FASTER BUILD COMMAND

ARG CACHEBUST=1

######################################### Viper Producer directory

RUN git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

RUN cp -R transactionalmachinelearning Viper-produce/transactionalmachinelearning

WORKDIR Viper-produce

RUN echo "*******************Viper for $CHIP PRODUCER**********************"

RUN if [ "$CHIP" = "ARM32" ] ; \
  then \
  unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPER\ *\ Linux\ ARM.zip && \
  chmod 755 viper-linux-arm ; \
elif [ "$CHIP" =  "ARM64" ] ; \
  then \
  unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPER\ *\ Linux\ ARM64.zip && \
  chmod 755 viper-linux-arm64 ; \
elif [ "$CHIP" = "AMD64" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPER\ *\ Linux\ AMD64.zip && \
  chmod 755 viper-linux-amd64 ; \ 
elif [ "$CHIP" = "MAC" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPER\ *\ Mac\ AMD64.zip && \
  chmod 755 viper-darwin-amd64 ; \ 
elif [ "$CHIP" = "WINDOWS" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPER\ *\ Windows\ AMD64.zip && \
  chmod 755 viper-windows-amd64 ; \ 
fi

RUN rm -rf transactionalmachinelearning
WORKDIR /
RUN chmod -R +x Viper-produce

######################################### Viper Preprocess directory

RUN cp -R transactionalmachinelearning Viper-preprocess/transactionalmachinelearning

WORKDIR Viper-preprocess

#RUN git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git
RUN echo "*******************Viper for $CHIP PREPROCESS**********************"

RUN if [ "$CHIP" = "ARM32" ] ; \
  then \
  unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPER\ *\ Linux\ ARM.zip && \
  chmod 755 viper-linux-arm ; \
elif [ "$CHIP" =  "ARM64" ] ; \
  then \
  unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPER\ *\ Linux\ ARM64.zip && \
  chmod 755 viper-linux-arm64 ; \
elif [ "$CHIP" = "AMD64" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPER\ *\ Linux\ AMD64.zip && \
  chmod 755 viper-linux-amd64 ; \ 
elif [ "$CHIP" = "MAC" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPER\ *\ Mac\ AMD64.zip && \
  chmod 755 viper-darwin-amd64 ; \ 
elif [ "$CHIP" = "WINDOWS" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPER\ *\ Windows\ AMD64.zip && \
  chmod 755 viper-windows-amd64 ; \ 
fi

RUN rm -rf transactionalmachinelearning
WORKDIR /
RUN chmod -R +x Viper-preprocess

RUN echo "*********************Downloading and Installing VIPERviz Visualization****************"
RUN mkdir Viperviz
RUN mkdir Viperviz/viperviz
RUN mkdir Viperviz/viperviz/views
RUN chmod -R +x Viperviz

RUN cp -R transactionalmachinelearning Viperviz/transactionalmachinelearning

WORKDIR Viperviz

#RUN git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

#RUN unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM.zip || true
RUN if [ "$CHIP" = "ARM32" ] ; \
  then \
  unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM.zip || true ; \
elif [ "$CHIP" = "ARM64" ] ; \
  then \
  unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM64.zip || true ; \
elif [ "$CHIP" = "AMD64" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPERviz\ *\ Linux\ AMD64.zip || true ; \ 
elif [ "$CHIP" = "MAC" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPERviz\ *\ Mac\ AMD64.zip || true ; \ 
elif [ "$CHIP" = "WINDOWS" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-VIPERviz\ *\ Windows\ AMD64.zip || true ; \ 
fi


RUN if [ "$CHIP" = "ARM32" ] ; \
  then \
  chmod 755 viperviz-linux-arm ; \
elif [ "$CHIP" = "ARM64" ] ; \
  then \
  chmod 755 viperviz-linux-arm64 ; \
elif [ "$CHIP" = "AMD64" ] ; \
  then \
  chmod 755 viperviz-linux-amd64 ; \ 
elif [ "$CHIP" = "MAC" ] ; \
  then \
  chmod 755 viperviz-darwin-amd64 ; \ 
elif [ "$CHIP" = "WINDOWS" ] ; \
  then \
  chmod 755 viperviz-windows-amd64 ; \ 
fi

RUN rm -rf transactionalmachinelearning
WORKDIR /

RUN chmod -R +x Viperviz

RUN echo "*********************Downloading and Installing HPDE AutoML********************"
RUN mkdir Hpde
RUN chmod -R +x Hpde

RUN cp -R transactionalmachinelearning Hpde/transactionalmachinelearning

WORKDIR Hpde

#RUN git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

RUN if [ "$CHIP" = "ARM32" ] ; \
  then \
  unzip transactionalmachinelearning/ARM-Chipset/MAADS-HPDE\ *\ Linux\ ARM.zip || true ; \
elif [ "$CHIP" = "ARM64" ] ; \
  then \
  unzip transactionalmachinelearning/ARM64-Chipset/MAADS-HPDE\ *\ Linux\ ARM64.zip || true ; \
elif [ "$CHIP" = "AMD64" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-HPDE\ *\ Linux\ AMD64.zip || true ; \
elif [ "$CHIP" = "MAC" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-HPDE\ *\ Mac\ AMD64.zip || true ; \
elif [ "$CHIP" = "WINDOWS" ] ; \
  then \
  unzip transactionalmachinelearning/MAADS-HPDE\ *\ Windows\ AMD64.zip || true ; \
fi

RUN if [ "$CHIP" = "ARM32" ] ; \
  then \
  chmod 755 hpde-linux-arm ; \
elif [ "$CHIP" = "ARM64" ] ; \
  then \
  chmod 755 hpde-linux-arm64 ; \
elif [ "$CHIP" = "AMD64" ] ; \
  then \
  chmod 755 hpde-linux-amd64 ; \ 
elif [ "$CHIP" = "MAC" ] ; \
  then \
  chmod 755 hpde-darwin-amd64 ; \ 
elif [ "$CHIP" = "WINDOWS" ] ; \
  then \
  chmod 755 hpde-windows-amd64 ; \ 
fi

WORKDIR /

RUN rm -rf transactionalmachinelearning

RUN chmod -R +x Hpde

##################################################CLONE RASPBERRY PI REPO #######################

RUN git clone --depth 1 https://github.com/smaurice101/raspberrypi.git

RUN chmod -R +x raspberrypi

RUN echo "Replace VIPER.ENV"

# ---------------------------------------------Update Viper.env ------------------------
RUN cp -rf raspberrypi/viper-env-file/viper.env Viper-produce/viper.env
RUN cp -rf raspberrypi/viper-env-file/viper.env Viper-preprocess/viper.env

RUN cp -rf raspberrypi/viper-env-file/viper.env Viperviz/viper.env

# ---------------------------------------------Download demo data ------------------------
RUN echo "Copy the TML-CISCO Solution Data"

RUN cp -rf raspberrypi/tml-cisco-pt/data/* Viper-produce/
WORKDIR Viper-produce
RUN chmod +x cisco_network_data.zip
RUN unzip cisco_network_data.zip

WORKDIR /
# ---------------------------------------------Download solution scripts ------------------------
RUN echo "Copy the TML-CISCO Solution Script"
RUN cp -rf raspberrypi/tml-cisco-pt/pythonscripts/pt-produce* Viper-produce/
RUN chmod -R +x Viper-produce

RUN cp -rf raspberrypi/tml-cisco-pt/pythonscripts/pt-preprocess* Viper-preprocess/
RUN chmod -R +x Viper-preprocess

RUN echo "PIP Install TML core packages"
RUN pip install maadstml

WORKDIR /

RUN cp -rf raspberrypi/tml-cisco-pt/tmux-shell-script/tmux-docker.sh tmux/tmux-docker.sh

RUN cp -rf raspberrypi/tml-cisco-pt/dashboard/viperviz.zip Viperviz/viperviz.zip
RUN chmod -R +x Viperviz
RUN chmod -R +x tmux

WORKDIR Viperviz
##########add delete here - to delete viperviz folder from main zip for viperviz binary
RUN rm -rf viperviz

RUN unzip viperviz.zip

WORKDIR /

RUN rm -rf raspberrypi

ENTRYPOINT ["/bin/bash","-c","while true; do sleep 1; done | ./tmux/tmux-docker.sh"]
