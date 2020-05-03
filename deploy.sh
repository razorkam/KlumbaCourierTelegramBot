#!/usr/bin/env bash

systemctl stop klumba_courier_bot
rm -f  /etc/systemd/system/klumba_courier_bot.service
cp -f ./klumba_courier_bot.service /etc/systemd/system/
systemctl start klumba_courier_bot
systemctl enable klumba_courier_bot
systemctl daemon-reload
