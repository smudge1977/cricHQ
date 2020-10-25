start cmd.exe /c dns-sd -R scoreboard _cricviewing._tcp. local 9090 localhost 127.0.0.1
call venv/Scripts/activate.bat
:loop
python CricHQServer.py >> %temp%/CricHQServer.log 2>>&1 | type %temp%/CricHQServer.log
goto loop
