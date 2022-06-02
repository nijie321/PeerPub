# 1920 (H) x 1080 (V) ,1280 (H) x 1024 (V),1280 (H) x 720 (V)
#NAME="/home/pi/image/"`cat /home/pi/deviceid``date`".jpg"
#echo $NAME
BoxID=$( cat /home/pi/deviceid )
echo $BoxID

fswebcam -r 1920x1080 -S 19 --set brightness=100% --set contrast=0% --loop 1  --no-banner /home/pi/image/"%F_%T_$BoxID".jpg
