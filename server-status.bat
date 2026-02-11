@echo off
REM Check server status
echo Checking production server status...
ssh hestia "systemctl status bank-converter --no-pager -l && echo '' && echo '=== Recent Logs ===' && journalctl -u bank-converter -n 10 --no-pager"
