#!/bin/bash

# Transactional Machine Learning (TML) with Kafka/Java/Python for ARM 32
# install java

CHIP="ARM32"
#CHIP="ARM64"
#CHIP="AMD64"

echo "Updating package index files"
sudo apt-get update

echo "Install WGET, GIT, UNZIP"
sudo apt install -y wget
sudo apt-get -y install git
sudo apt-get -y install unzip

echo "Downloading and Installing TML technologies "
echo "Downloading and Installing VIPER"
sudo mkdir Viper
sudo chmod +x Viper
sudo cd Viper

sudo git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

if [$CHIP -eq "ARM32"]
  then
  sudo unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPER\ *\ Linux\ ARM.zip
  sudo chmod 755 viper-linux-arm
elif [$CHIP -eq "ARM64"]
  then
  sudo unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPER\ *\ Linux\ ARM64.zip
  sudo chmod 755 viper-linux-arm64
elif [$CHIP -eq "AMD64"]
  then
  sudo unzip transactionalmachinelearning/MAADS-VIPER\ *\ Linux\ AMD64.zip
  sudo chmod 755 viper-linux-amd64  
fi

cd ..

echo "Downloading and Installing VIPER Visualization"
sudo mkdir Viperviz
sudo chmod +x Viperviz
sudo cd Viperviz

sudo git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

if [$CHIP -eq "ARM32"]
  then
  sudo unzip transactionalmachinelearning/ARM-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM.zip
  sudo chmod 755 viperviz-linux-arm
elif [$CHIP -eq "ARM64"]
  then
  sudo unzip transactionalmachinelearning/ARM64-Chipset/MAADS-VIPERviz\ *\ Linux\ ARM64.zip
  sudo chmod 755 viperviz-linux-arm64
elif [$CHIP -eq "AMD64"]
  then
  sudo unzip transactionalmachinelearning/MAADS-VIPERviz\ *\ Linux\ AMD64.zip
  sudo chmod 755 viperviz-linux-amd64  
fi

echo "Downloading and Installing HPDE AutoML"
sudo mkdir Hpde
sudo chmod +x Hpde
sudo cd Hpde

sudo git clone --depth 1 https://github.com/smaurice101/transactionalmachinelearning.git

if [$CHIP -eq "ARM32"]
  then
  sudo unzip transactionalmachinelearning/ARM-Chipset/MAADS-HPDE\ *\ Linux\ ARM.zip
  sudo chmod 755 hpde-linux-arm
elif [$CHIP -eq "ARM64"]
  then
  sudo unzip transactionalmachinelearning/ARM64-Chipset/MAADS-HPDE\ *\ Linux\ ARM64.zip
  sudo chmod 755 hpde-linux-arm64
elif [$CHIP -eq "AMD64"]
  then
  sudo unzip transactionalmachinelearning/MAADS-HPDE\ *\ Linux\ AMD64.zip
  sudo chmod 755 hpde-linux-amd64  
fi


echo "Downloading and Installing KAFKA"
sudo cd ..
sudo mkdir Kafka
sudo chmod +x Kafka
sudo cd Kafka
wget https://archive.apache.org/dist/kafka/3.0.0/kafka_2.13-3.0.0.tgz
sudo tar xzf kafka_2.13-3.0.0.tgz

sudo export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"
sudo PWD=`pwd`
sudo PATH="$PATH:$PWD/Kafka/kafka_2.13-3.0.0/bin"

cd ..
echo "Install TMUX"
sudo apt-get install tmux

echo "Install Mariadb"
sudo apt install mariadb-server
sudo mysql_secure_installation
# RUN: sudo mysql -u root
# Execute: SET PASSWORD FOR 'root'@'localhost' = PASSWORD('raspberry'); 
# GRANT ALL PRIVILEGES on *.* to 'root'@'localhost' IDENTIFIED BY 'raspberry'; 
# FLUSH PRIVILEGES;

echo "Replace VIPER.ENV"
sudo git clone --depth 1 https://github.com/smaurice101/raspberrypi.git
sudo cp -rf raspberrypi/viper-env-file/viper.env Viper/viper.env
sudo cp -rf raspberrypi/viper-env-file/viper.env Viperviz/viper.env

echo "Copy the IotSolution Scripts"
cd ..
sudo mkdir IotSolution
sudo cp -rf raspberrypi/iotsolution-scripts-data/* /

sudo cp -rf raspberrypi/tmux-shell-script/tmux.sh tmux/tmux.sh

sudo cp -rf raspberrypi/iot-dashboard-html/viperviz.zip /Viperviz
sudo cd Viperviz
sudo unzip viperviz.zip


echo "Downloading and Installing Python 3.9"
sudo cd ..
sudo mkdir Python
sudo chmod +x Python
sudo cd Python


sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tar wget vim

sudo wget https://www.python.org/ftp/python/3.9.15/Python-3.9.15.tgz
sudo tar -zxvf Python-3.9.15.tgz
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

echo "Installing Java"
sudo apt install default-jdk

echo "Installing Python 3.9"
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tar wget vim

