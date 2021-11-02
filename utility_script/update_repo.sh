#!/bin/bash


##cd /home/pi/openbehavior/ && rm -rf PeerPub/ && cd /home/pi/openbehavior/ && git clone https://www.github.com/nijie321/PeerPub.git

cd /home/pi/openbehavior/PeerPub/ && git pull

echo $(date +"%m-%d-%y %T") $(git log -1 --pretty=oneline) >> "/home/pi/SocialDrinking/${BOXID}_update"


bash /home/pi/openbehavior/PeerPub/wifi-network/rsync.sh
