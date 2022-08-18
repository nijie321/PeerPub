# 1920 (H) x 1080 (V) ,1280 (H) x 1024 (V),1280 (H) x 720 (V)
#NAME="/home/pi/image/"`cat /home/pi/deviceid``date`".jpg"
#echo $NAME
#BoxID=$( cat /home/pi/deviceid )
#echo $BoxID
echo $1
echo $2
echo $3
mkdir "/home/pi/image/$(date +"%Y-%m-%d_$3_S$2")"

timeout $1 nice -n 10 fswebcam -r 1920x1080 -S 19 --set brightness=100% --set contrast=0% --loop 1  --no-banner /home/pi/image/$(date +"%Y-%m-%d_$3_S$2")/"%F_%T_$3_S$2".jpg

