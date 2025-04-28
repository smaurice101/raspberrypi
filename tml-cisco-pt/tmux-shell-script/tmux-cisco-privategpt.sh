 #!/bin/bash
 
# Developed by: Sebastian Maurice
# Date: 2023-05-22
########################### START ZOOKEEPER and KAFKA
 export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"
 export  userbasedir=`pwd`
 MYIP=$(ip route get 8.8.8.8 | awk '{ print $7; exit }')
 export MYIP
 CHIP2=${CHIP}
 runtype=${RUNTYPE}
 brokerhostport=${BROKERHOSTPORT}
 mainkafkatopic=${KAFKAPRODUCETOPIC}

 vipervizport=${VIPERVIZPORT}
 export vipervizport

 cloudusername=${CLOUDUSERNAME}
 cloudpassword=${CLOUDPASSWORD}

 export cloudusername
 export cloudpassword

 cloudusername=$(sed 's/[]\/$*.^[]/\\&/g'  <<<"$cloudusername")
 cloudpassword=$(sed 's/[]\/$*.^[]/\\&/g'  <<<"$cloudpassword")
 
 export cloudusername
 export cloudpassword
 export brokerhostport
 export runtype
 export mainkafkatopic
 
 chip=$(echo "$CHIP2" | tr '[:upper:]' '[:lower:]')
 mainos="linux"

 if [ "$chip" = "arm32" ]; then 
    export chip="arm"
    export mainos
 elif [ "$chip" = "mac" ]; then 
    export chip="amd64"
    export mainos="darwin"   
 elif [ "$chip" = "macarm64" ]; then 
    export chip="arm64"
    export mainos="darwin"       
 else
    export chip 
    export mainos
 fi

service mariadb restart 2>/dev/null
mysql -u root -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('raspberry');" 2>/dev/null
mysql -u root -e "GRANT ALL PRIVILEGES on *.* to 'root'@'localhost' IDENTIFIED BY 'raspberry';" 2>/dev/null
mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null

# sudo mount -o remount,rw /partition/identifier $userbasedir

 kill -9 $(lsof -i:9092 -t) 2> /dev/null
 kill -9 $(lsof -i:2181 -t) 2> /dev/null
 
 sleep 2

 tmux new -d -s zookeeper
 tmux send-keys -t zookeeper 'cd $userbasedir/Kafka/kafka_2.13-3.0.0/bin' ENTER
 tmux send-keys -t zookeeper './zookeeper-server-start.sh $userbasedir/Kafka/kafka_2.13-3.0.0/config/zookeeper.properties' ENTER

 sleep 4

 tmux new -d -s kafka 
 tmux send-keys -t kafka 'cd $userbasedir/Kafka/kafka_2.13-3.0.0/bin' ENTER
 tmux send-keys -t kafka './kafka-server-start.sh $userbasedir/Kafka/kafka_2.13-3.0.0/config/server.properties' ENTER

sleep 10
 ########################## SETUP VIPER/HPDE/VIPERVIZ Binaries For Transactional Machine Learning 

if [ "$runtype" == "1" ]; then  
  # STEP 1: Produce Data to Kafka
  # STEP 1a: RUN VIPER Binary
   tmux new -d -s produce-cisco-data-viper-8000 
   tmux send-keys -t produce-cisco-data-viper-8000 'cd $userbasedir/Viper-produce' ENTER
   tmux send-keys -t produce-cisco-data-viper-8000 '$userbasedir/Viper-produce/viper-$mainos-$chip' ENTER
sleep 7

 # STEP 2b: RUN PYTHON Script  
   tmux new -d -s produce-cisco-data-python-8000 
   tmux send-keys -t produce-cisco-data-python-8000 'cd $userbasedir/Viper-produce' ENTER
   tmux send-keys -t produce-cisco-data-python-8000 'python $userbasedir/Viper-produce/pt-produce-localfile-external.py' ENTER
 fi

if [ "$runtype" == "2" ]; then  
   tmux new -d -s produce-cisco-data-viper-8000 
   tmux send-keys -t produce-cisco-data-viper-8000 'cd $userbasedir/Viper-produce' ENTER
   tmux send-keys -t produce-cisco-data-viper-8000 "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viper-produce/viper.env" ENTER   
   tmux send-keys -t produce-cisco-data-viper-8000 "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viper-produce/viper.env" ENTER      
   tmux send-keys -t produce-cisco-data-viper-8000 "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viper-produce/viper.env" ENTER      
   tmux send-keys -t produce-cisco-data-viper-8000 '$userbasedir/Viper-produce/viper-$mainos-$chip' ENTER
sleep 20

 # STEP 2b: RUN PYTHON Script  
   tmux new -d -s produce-cisco-data-python-8000 
   tmux send-keys -t produce-cisco-data-python-8000 'cd $userbasedir/Viper-produce' ENTER
   tmux send-keys -t produce-cisco-data-python-8000 'python $userbasedir/Viper-produce/pt-produce-localfile-external.py' ENTER
 fi

# -1 instructor needs to have cisco packet tracer running
if [[ "$runtype" == "0" || "$runtype" == "-1" ]]; then  
  # STEP 1: Produce Data to Kafka
  # STEP 1a: RUN VIPER Binary

   tmux new -d -s produce-cisco-data-viper-8000 
   tmux send-keys -t produce-cisco-data-viper-8000 'cd $userbasedir/Viper-produce' ENTER
   tmux send-keys -t produce-cisco-data-viper-8000 "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viper-produce/viper.env" ENTER   
   tmux send-keys -t produce-cisco-data-viper-8000 "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viper-produce/viper.env" ENTER      
   tmux send-keys -t produce-cisco-data-viper-8000 "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viper-produce/viper.env" ENTER      
   tmux send-keys -t produce-cisco-data-viper-8000 '$userbasedir/Viper-produce/viper-$mainos-$chip' ENTER
sleep 20

 # STEP 2b: RUN PYTHON Script  
   tmux new -d -s produce-cisco-data-python-8000 
   tmux send-keys -t produce-cisco-data-python-8000 'cd $userbasedir/Viper-produce' ENTER
   tmux send-keys -t produce-cisco-data-python-8000 'python $userbasedir/Viper-produce/pt-produce-external.py' ENTER
 fi

# runtype=-1 then this is instructor so does not need to preprocess
if [[ "$runtype" == "1" || "$runtype" == "0" ]]; then   
  # STEP 2: Preprocess Data from Kafka
  # STEP 2a: RUN VIPER Binary
   tmux new -d -s preprocess-cisco-data-viper-8001
   tmux send-keys -t preprocess-cisco-data-viper-8001 'cd $userbasedir/Viper-preprocess' ENTER
   tmux send-keys -t preprocess-cisco-data-viper-8001 "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viper-preprocess/viper.env" ENTER   
   tmux send-keys -t preprocess-cisco-data-viper-8001 "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viper-preprocess/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-8001 "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viper-preprocess/viper.env" ENTER      

   tmux send-keys -t preprocess-cisco-data-viper-8001 '$userbasedir/Viper-preprocess/viper-$mainos-$chip' ENTER

 sleep 20

   tmux new -d -s preprocess-cisco-data-python-8001
   tmux send-keys -t preprocess-cisco-data-python-8001 'cd $userbasedir/Viper-preprocess' ENTER 
   tmux send-keys -t preprocess-cisco-data-python-8001 'python $userbasedir/Viper-preprocess/pt-preprocess-external.py' ENTER

   tmux new -d -s preprocess-cisco-data-viper-pgpt
   tmux send-keys -t preprocess-cisco-data-viper-pgpt 'cd $userbasedir/Viper-preprocess-pgpt' ENTER
   tmux send-keys -t preprocess-cisco-data-viper-pgpt "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viper-preprocess-pgpt/viper.env" ENTER   
   tmux send-keys -t preprocess-cisco-data-viper-pgpt "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viper-preprocess-pgpt/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-pgpt "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viper-preprocess-pgpt/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-pgpt '$userbasedir/Viper-preprocess-pgpt/viper-$mainos-$chip' ENTER
sleep 20
   
   tmux new -d -s preprocess-cisco-data-python-pgpt
   tmux send-keys -t preprocess-cisco-data-python-pgpt 'cd $userbasedir/Viper-preprocess-pgpt' ENTER 
   tmux send-keys -t preprocess-cisco-data-python-pgpt 'python $userbasedir/Viper-preprocess-pgpt/privategpt-tml-maadstml-external.py' ENTER
   
fi 

# runtype=-2 then this is student preprocess for presentation
if [[ "$runtype" == "-2" || "$runtype" == "2" ]]; then   
   tmux new -d -s preprocess-cisco-data-viper-8001
   tmux send-keys -t preprocess-cisco-data-viper-8001 'cd $userbasedir/Viper-preprocess' ENTER
   tmux send-keys -t preprocess-cisco-data-viper-8001 "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viper-preprocess/viper.env" ENTER   
   tmux send-keys -t preprocess-cisco-data-viper-8001 "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viper-preprocess/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-8001 "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viper-preprocess/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-8001 '$userbasedir/Viper-preprocess/viper-$mainos-$chip' ENTER
sleep 20
   tmux new -d -s preprocess-cisco-data-python-8001
   tmux send-keys -t preprocess-cisco-data-python-8001 'cd $userbasedir/Viper-preprocess' ENTER    
   tmux send-keys -t preprocess-cisco-data-python-8001 'python $userbasedir/Viper-preprocess/pt-preprocess-external.py' ENTER

   tmux new -d -s preprocess-cisco-data-viper-pgpt
   tmux send-keys -t preprocess-cisco-data-viper-pgpt 'cd $userbasedir/Viper-preprocess-pgpt' ENTER
   tmux send-keys -t preprocess-cisco-data-viper-pgpt "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viper-preprocess-pgpt/viper.env" ENTER   
   tmux send-keys -t preprocess-cisco-data-viper-pgpt "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viper-preprocess-pgpt/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-pgpt "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viper-preprocess-pgpt/viper.env" ENTER      
   tmux send-keys -t preprocess-cisco-data-viper-pgpt '$userbasedir/Viper-preprocess-pgpt/viper-$mainos-$chip' ENTER
sleep 20
   
   tmux new -d -s preprocess-cisco-data-python-pgpt
   tmux send-keys -t preprocess-cisco-data-python-pgpt 'cd $userbasedir/Viper-preprocess-pgpt' ENTER 
   tmux send-keys -t preprocess-cisco-data-python-pgpt 'python $userbasedir/Viper-preprocess-pgpt/privategpt-tml-maadstml-external.py' ENTER
   
 fi 

# STEP 5: START Visualization Viperviz 
 
if [ "$runtype" != "-1" ]; then   
   tmux new -d -s visualization-cisco-viperviz-$vipervizport 
   tmux send-keys -t visualization-cisco-viperviz-$vipervizport 'cd $userbasedir/Viperviz' ENTER

   tmux send-keys -t visualization-cisco-viperviz-$vipervizport "sed -i 's/127.0.0.1:9092/$brokerhostport/g' $userbasedir/Viperviz/viper.env" ENTER   
   tmux send-keys -t visualization-cisco-viperviz-$vipervizport "sed -i 's/CLOUD_USERNAME=/CLOUD_USERNAME=$cloudusername/g' $userbasedir/Viperviz/viper.env" ENTER      
   tmux send-keys -t visualization-cisco-viperviz-$vipervizport "sed -i 's/CLOUD_PASSWORD=/CLOUD_PASSWORD=$cloudpassword/g' $userbasedir/Viperviz/viper.env" ENTER      
   tmux send-keys -t visualization-cisco-viperviz-$vipervizport '$userbasedir/Viperviz/viperviz-$mainos-$chip 0.0.0.0 $vipervizport' ENTER
fi
 
