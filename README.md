# raspberrypi
IoT: TML and Kafka on Raspberry PI
IF having issues with java you may need to re-install

sudo apt install --reinstall default-jre default-jdk default-jre-headless default-jdk-headless openjdk-11-jdk openjdk-11-jdk-headless openjdk-11-jre openjdk-11-jre-headless openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre openjdk-8-jre-headless

Note you may need to run: 
1. sudo rm /var/lib/dpkg/info/* 
2. sudo dpkg --configure -a

If you have MySQL issues try this:
1. ps -A|grep mysql
2. sudo pkill mysql
3. ps -A|grep mysqld
4. sudo pkill mysqld
5. service mysql restart

in sudo nano /etc/mysql/my.cnf:
port = 3306
