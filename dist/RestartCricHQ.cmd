@echo off
cd\CricHQ
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "datestamp=%YYYY%%MM%%DD%" & set "timestamp=%HH%%Min%%Sec%"
set "fullstamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"
echo datestamp: "%datestamp%"
echo timestamp: "%timestamp%"
echo fullstamp: "%fullstamp%"
IF "%SCOREBOARDNAME%"=="" (SET SCOREBOARDNAME=TestScoreboard)
echo SCOREBOARDNAME is %SCOREBOARDNAME%

taskkill /IM "async.exe" /F
taskkill /IM "dns-sd.exe" /F
timeout 5
rem c:\CricHQ\run.cmd
start cmd.exe /c dns-sd -R %SCOREBOARDNAME% _cricviewing._tcp. local 9090 localhost 127.0.0.1
:loop
start async 2>&1 | tee ChricHQServer.%fullstamp%.log
mkdir %fullstamp%
copy *.json %fullstamp%
copy ChricHQServer.%fullstamp%.log %fullstamp%