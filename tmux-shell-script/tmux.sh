 #!/bin/bash
 

########################### START ZOOKEEPER and KAFKA
 export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"
 cd ..
 export  userbasedir=`pwd`
 export CHIP="ARM32"

 MYIP=$(ip route get 8.8.8.8 | awk '{ print $7; exit }')
 export MYIP
 CHIP2=${CHIP}
 chip=$(echo "$CHIP2" | tr '[:upper:]' '[:lower:]')

 if [ "$chip" = "arm32" ]; then 
    export chip="arm"
 else
    export chip
 fi
 
# sudo mount -o remount,rw /partition/identifier $userbasedir

 sudo kill -9 $(sudo lsof -i:9092 -t) 2> /dev/null
 sudo kill -9 $(sudo lsof -i:2181 -t) 2> /dev/null
 
 sleep 5
 service mariadb restart 2>/dev/null
 mysql -u root -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('raspberry');" 2>/dev/null
 mysql -u root -e "GRANT ALL PRIVILEGES on *.* to 'root'@'localhost' IDENTIFIED BY 'raspberry';" 2>/dev/null
 mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null

 tmux new -d -s zookeeper
 tmux send-keys -t zookeeper 'cd $userbasedir/Kafka/kafka_2.13-3.0.0/bin' ENTER
 tmux send-keys -t zookeeper 'sudo ./zookeeper-server-start.sh $userbasedir/Kafka/kafka_2.13-3.0.0/config/zookeeper.properties' ENTER


 sleep 20

 tmux new -d -s kafka 
 tmux send-keys -t kafka 'cd $userbasedir/Kafka/kafka_2.13-3.0.0/bin' ENTER
 tmux send-keys -t kafka 'sudo ./kafka-server-start.sh $userbasedir/Kafka/kafka_2.13-3.0.0/config/server.properties' ENTER

sleep 45
 ########################## SETUP VIPER/HPDE/VIPERVIZ Binaries For Transactional Machine Learning 
 
# STEP 1: Produce Data to Kafka
# STEP 1a: RUN VIPER Binary
  
 tmux new -d -s produce-iot-data-viper-8000 
 tmux send-keys -t produce-iot-data-viper-8000 'cd $userbasedir/Viper' ENTER
 tmux send-keys -t produce-iot-data-viper-8000 'sudo $userbasedir/Viper/viper-linux-$chip 127.0.0.1 8000' ENTER

 sleep 25
# STEP 1b: RUN PYTHON Script 
 tmux new -d -s produce-iot-data-python-8000 
 tmux send-keys -t produce-iot-data-python-8000 'cd $userbasedir/IotSolution' ENTER
 tmux send-keys -t produce-iot-data-python-8000 'python $userbasedir/IotSolution/produce-iot-customdata.py' ENTER
 
# STEP 2: Preprocess Data from Kafka
# STEP 2a: RUN VIPER Binary
 tmux new -d -s preprocess-data-viper-8001
 tmux send-keys -t preprocess-data-viper-8001 'cd $userbasedir/Viper' ENTER
 tmux send-keys -t preprocess-data-viper-8001 'sudo $userbasedir/Viper/viper-linux-$chip 127.0.0.1 8001' ENTER

 tmux new -d -s preprocess2-data-viper-8002
 tmux send-keys -t preprocess2-data-viper-8002 'cd $userbasedir/Viper' ENTER 
 tmux send-keys -t preprocess2-data-viper-8002 'sudo $userbasedir/Viper/viper-linux-$chip 127.0.0.1 8002' ENTER
 
sleep 25

# STEP 2b: RUN PYTHON Script  
 tmux new -d -s preprocess-data-python-8001
 tmux send-keys -t preprocess-data-python-8001 'cd $userbasedir/IotSolution' ENTER 
 tmux send-keys -t preprocess-data-python-8001 'python $userbasedir/IotSolution/preprocess-iot-monitor-customdata.py' ENTER
  

 tmux new -d -s preprocess2-data-python-8002
 tmux send-keys -t preprocess2-data-python-8002 'cd $userbasedir/IotSolution' ENTER
 tmux send-keys -t preprocess2-data-python-8002 'python $userbasedir/IotSolution/preprocess2-iot-monitor-customdata.py' ENTER


# STEP 5: START Visualization Viperviz 
 tmux new -d -s visualization-viperviz-9005 
 tmux send-keys -t visualization-viperviz-9005 'cd $userbasedir/Viperviz' ENTER
 tmux send-keys -t visualization-viperviz-9005 'sudo $userbasedir/Viperviz/viperviz-linux-$chip $MYIP 9005' ENTER
 
