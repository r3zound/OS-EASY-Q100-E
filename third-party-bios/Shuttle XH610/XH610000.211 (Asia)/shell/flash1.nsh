echo -off
cls
ver
date
time
echo "  "

echo Checking ROM file .....
ChkSHUid_x64.efi 41251297
if not %lasterror% == 0 then
goto end
endif

:flash
echo "1st"
AfuEfix64.efi XH610.bin /p /b /n /r
if not %lasterror% == 0 then
goto end
endif

copy ..\times.txt ..\once.txt

echo "    "
echo The machine will reboot and flash do the 2nd flashing, please keep your machine is on and do not turn the power off.
echo "    "   

reset -w

:end
echo "  "
echo "Update not sucessful."
echo "  "

cd ..