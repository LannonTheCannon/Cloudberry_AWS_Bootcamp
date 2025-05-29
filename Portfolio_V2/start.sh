#!/bin/bash
source ~/Cloudberry_AWS_Bootcamp/Portfolio_V2/venv/bin/activate
cd ~/Cloudberry_AWS_Bootcamp/Portfolio_V2
nohup gunicorn -w 4 -b 0.0.0.0:5001 app:app &
