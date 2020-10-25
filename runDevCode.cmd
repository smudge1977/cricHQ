call venv\Scripts\activate.bat
:loop

echo start
"CricHQServer.py"  2>&1 
echo end

goto loop