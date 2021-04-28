start cmd.exe /c dns-sd -R scoreboard _cricviewing._tcp. local 9090 localhost 127.0.0.1
:loop
async 2>&1 | tee ChricHQServer.log
echo crashed and looped >> crash.log

goto loop

rem call venv/Scripts/activate.bat
rem :loop
rem python CricHQServer.py >> %temp%/CricHQServer.log 2>>&1 | type %temp%/CricHQServer.log
rem goto loop
