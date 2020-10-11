if not exist venv\. python -m venv venv
call venv\Scripts\activate.bat
pip3 install -r requirements.txt
pip3 install pyinstaller
pyinstaller --onefile CricHQServer.py
