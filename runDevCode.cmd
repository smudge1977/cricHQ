call venv\Scripts\activate.bat
:loop

echo start
"CricHQServer.py"  2>crash.log 
echo end

goto loop