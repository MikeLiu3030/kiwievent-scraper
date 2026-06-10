
@echo off
title kiwi-event-scraper
cd /d D:\WORK\kiwisquare\kiwiEvent-scraper
echo ================================== >> task_run.log 
echo [%date% %time%] start script >> task_run.log

call venv\Scripts\activate
python app.py >> task_run.log 2>&1


