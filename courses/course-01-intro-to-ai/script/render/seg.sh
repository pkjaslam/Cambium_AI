#!/bin/bash
cd ~/build/video
for i in $(seq $1 $2); do
  n=$(printf "%02d" $i)
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 audio/a-$n.mp3)
  t=$(python3 -c "print(round($d + 1.6, 3))")
  ffmpeg -y -v error -loop 1 -framerate 12 -i frames/f-$n.png -i audio/a-$n.mp3 \
    -af "adelay=600|600,apad" -t $t \
    -vf "scale=1920:1080,format=yuv420p" \
    -c:v libx264 -preset ultrafast -tune stillimage -crf 20 -r 12 \
    -c:a aac -b:a 128k -ar 44100 -ac 2 segs/s-$n.mp4
  echo -n "$i "
done
echo done
