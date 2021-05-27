@echo off 
rem # Python build script after pulling from Repo
rem # What is the actual file we are building? Needs to be in the root of the repo currently

SET PACKAGE_NAME=async.py 

echo Should run packaging\build.cmd from root of git Repo
if not exist .\.git goto no_git
if not exist %PACKAGE_NAME% goto error
git fetch
git status -s
git rev-parse --short HEAD > tmpFile 
set /p GITREV= < tmpFile 
echo Git rev %GITREV%
del tmpFile
echo GITREV="%GITREV%" > _gitrev.py

if not exist venv\. python -m venv venv
call venv\Scripts\activate.bat
pip3 install -r requirements.txt
pip3 install pyinstaller
pyinstaller --onefile %PACKAGE_NAME%

rem xcopy dist\* "G:\My Drive\Repo\Windows\CricHQServer" /s/y
goto :EOF

:error
echo no %PACKAGE_NAME% found
exit 99

:no_git
echo Not a git repo
exit 99
