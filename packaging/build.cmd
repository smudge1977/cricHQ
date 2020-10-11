python3 -m venv venv
call venv/Scripts/activate.cmd
pip3 install -r requirements.txt
pyinstaller --onefile CricHQServer.py
