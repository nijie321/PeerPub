#!/bin/bash

# introduce a small random delay so that the server does not get too many requrests at the same time.
delay=`shuf -i1-3 -n1` 

# make sure wlan0 is up
#ifconfig wlan0 up
#while [ `sudo ifconfig wlan0 |grep broadcast |wc -l` -ne 1 ]
#	do
#	sleep 2
#	cnt=$[$cnt+1]
#	if [ $cnt -eq 30 ] # max 60 sec  
#		then 
#			break
#	fi
#done

BoxID=$( cat /home/pi/deviceid )
rsync -auvp -e ssh /home/pi/image/ hao@172.21.216.122:/disks/PeerPubImages/
rm -rf `find /home/pi/image/* -mtime +15`

# remove files older than 15 days but keep stepsize and git update files
rm `find /home/pi/SocialDrinking/* -mtime +15 |grep -v 'steps\|update'` 

gzip -f /home/pi/SocialDrinking/*csv

rsync -auvp -e ssh /home/pi/SocialDrinking/ root@149.56.128.122:~/Dropbox/Pies/SocialDrinking/ 
sleep 15
#sync one more time
#rsync -auvp -e ssh /home/pi/SocialDrinking/ root@149.56.128.122:~/Dropbox/Pies/SocialDrinking/ 

rsync -auvp -e ssh /home/pi/image/ root@149.56.128.122:~/Dropbox/Pies/Images/$BoxID/

echo "Use sync key to sync data again, or scan any other key to reboot"
read var
if [[ $var = "0086eafa" || $var = "002d5494" ]]; then
        echo "Sync data again"
rsync -auvp -e ssh /home/pi/SocialDrinking/ root@149.56.128.122:~/Dropbox/Pies/SocialDrinking/
echo "If sync fails, scan sync key to sync again after reboot"
sleep 15
sudo reboot -f
else
        echo "reboot system"
sudo reboot -f

fi
