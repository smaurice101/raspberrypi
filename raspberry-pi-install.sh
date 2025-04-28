#!/bin/bash

# Transactional Machine Learning (TML) with Kafka/Java/Python for ARM 32
# install java

CHIP="ARM32"
#CHIP="ARM64"
#CHIP="AMD64"

#echo "Updating package index files"
#sudo apt-get update

sudo pkill -9 apt

echo "Install WGET, GIT, UNZIP"
sudo apt install -y wget
sudo apt install -y git
sudo apt install -y unzip


echo "Downloading and Installing TML technologies "
echo "Downloading and Installing VIPER"
sudo mkdir Viper
sudo chmod -R +x Viper
cd Viper

yes Y | sudo git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git
echo "*******************Viper for $CHIP**********************"

if [ "$CHIP" = "ARM32" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPER\ *\ Linux\ ARM.zip
  sudo chmod 755 viper-linux-arm
elif [ "$CHIP" =  "ARM64" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPER\ *\ Linux\ ARM64.zip
  sudo chmod 755 viper-linux-arm64
elif [ "$CHIP" = "AMD64" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/MAADS-VIPER\ *\ Linux\ AMD64.zip
  sudo chmod 755 viper-linux-amd64  
fi

sudo rm -rf transactionalmachinelearning
cd ..
sudo chmod -R +x Viper

echo "*********************Downloading and Installing VIPERviz Visualization****************"
sudo mkdir Viperviz
sudo mkdir Viperviz/viperviz
sudo mkdir Viperviz/viperviz/views
sudo chmod -R +x Viperviz

cd Viperviz
sudo mkdir viperviz

yes Y | sudo git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

if [ "$CHIP" = "ARM32" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM.zip
  sudo chmod 755 viperviz-linux-arm
elif [ "$CHIP" = "ARM64" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM64.zip
  sudo chmod 755 viperviz-linux-arm64
elif [ "$CHIP" = "AMD64" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/MAADS-VIPERviz\ *\ Linux\ AMD64.zip
  sudo chmod 755 viperviz-linux-amd64  
fi

sudo rm -rf transactionalmachinelearning
cd ..
sudo chmod -R +x Viperviz


echo "*********************Downloading and Installing HPDE AutoML********************"
sudo mkdir Hpde
sudo chmod -R +x Hpde
cd Hpde

yes Y | sudo git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

if [ "$CHIP" = "ARM32" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/ARM-Chipset/MAADS-HPDE\ *\ Linux\ ARM.zip
  sudo chmod 755 hpde-linux-arm
elif [ "$CHIP" = "ARM64" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/ARM64-Chipset/MAADS-HPDE\ *\ Linux\ ARM64.zip
  sudo chmod 755 hpde-linux-arm64
elif [ "$CHIP" = "AMD64" ]
  then
  yes Y | sudo unzip transactionalmachinelearning/MAADS-HPDE\ *\ Linux\ AMD64.zip
  sudo chmod 755 hpde-linux-amd64  
fi

sudo rm -rf transactionalmachinelearning

echo "Downloading and Installing KAFKA"
cd ..
sudo chmod -R +x Hpde

sudo mkdir Kafka
sudo chmod -R +x Kafka

cd Kafka
yes Y | sudo wget -O kafka_2.13-3.0.0.tgz https://archive.apache.org/dist/kafka/3.0.0/kafka_2.13-3.0.0.tgz
sudo chmod +x kafka_2.13-3.0.0.tgz

yes Y | sudo tar xzf kafka_2.13-3.0.0.tgz

export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"
export PWD=`pwd`
export PATH="$PATH:$PWD/Kafka/kafka_2.13-3.0.0/bin"

sudo rm -rf kafka_2.13-3.0.0.tgz
cd ..
sudo chmod -R +x Kafka


echo "Install TMUX"
sudo apt -y install tmux
sudo mkdir tmux

echo "Install Mariadb"
sudo apt install mariadb-server
# sudo mysql_secure_installation
# RUN: sudo mysql -u root
# Execute: SET PASSWORD FOR 'root'@'localhost' = PASSWORD('raspberry'); 
# GRANT ALL PRIVILEGES on *.* to 'root'@'localhost' IDENTIFIED BY 'raspberry'; 
# FLUSH PRIVILEGES;

echo "Replace VIPER.ENV"
sudo git clone --depth 1 https://github.com/smaurice101/raspberrypi.git

sudo chmod -R +x raspberrypi

sudo cp -rf raspberrypi/viper-env-file/viper.env Viper/viper.env
sudo cp -rf raspberrypi/viper-env-file/viper.env Viperviz/viper.env

echo "Copy the IotSolution Scripts"

sudo mkdir IotSolution
sudo cp -rf raspberrypi/iotsolution-scripts-data/* IotSolution/

################# IOT DATA
cd IotSolution
yes Y | sudo wget --no-check-certificate 'https://docs.google.com/uc?export=download&id=1yRgDYrWnHu74NYX9GMAVDjR10ZyfoZvh' -O IoTData.zip
sudo chmod +x IoTData.zip
yes Y | sudo unzip IoTData.zip

yes Y | sudo wget --no-check-certificate 'https://docs.google.com/uc?export=download&id=1_RICecxEZUjuCfm_MxPGwrOXxQ5w179O' -O dsntmlidmain.csv
sudo chmod +x dsntmlidmain.csv
sudo rm -rf IoTData.zip
cd ..

sudo cp -rf raspberrypi/tmux-shell-script/tmux.sh tmux/tmux.sh

sudo cp -rf raspberrypi/iot-dashboard-html/viperviz.zip Viperviz/
sudo chmod -R +x IotSolution
sudo chmod -R +x Viperviz
sudo chmod -R +x tmux

cd Viperviz
yes Y | sudo unzip viperviz.zip
cd ~

sudo rm -rf raspberrypi


echo "Installing Java"
yes Y | sudo apt install default-jdk

######################################################

exit 1

#####################################################

echo "Downloading and Installing Python 3.9"

sudo mkdir Python
sudo chmod -R +x Python
cd Python


yes Y | sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tar wget vim

yes Y | sudo wget -O Python-3.9.15.tgz https://www.python.org/ftp/python/3.9.15/Python-3.9.15.tgz
sudo chmod -R +x Python-3.9.15.tgz
sudo tar -zxvf Python-3.9.15.tgz
sudo chmod -R +x Python-3.9.15

cd Python-3.9.15/
sudo ./configure --enable-optimizations
sudo make altinstall
sudo pip install --upgrade pip

echo "PIP Install TML core packages"
sudo pip install maadstml
sudo pip install requests
sudo pip install nest_asyncio
sudo pip install joblib
sudo pip install asyncio


echo "Confirming Python install"
python –version

#echo "Installing Python 3.9"
#sudo apt install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tar wget vim

