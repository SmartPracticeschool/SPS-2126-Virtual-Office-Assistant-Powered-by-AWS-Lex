#!/bin/bash
echo
echo "You have the following devices in /proc/asound/cards"
echo "======="
cat /proc/asound/cards
echo
echo
echo -n "Enter your default card id: "
read -n 1 cardid
echo
echo Setting to card id $cardid
cat > ~/.asoundrc <<EOF
defaults.ctl.card $cardid
defaults.pcm.card $cardid
defaults.pcm.device 0
EOF
echo Testing audio
aplay /usr/share/sounds/alsa/Front_Center.wav > /dev/null 2>&1  &
aplay /usr/share/sounds/alsa/Front_Right.wav > /dev/null 2>&1
