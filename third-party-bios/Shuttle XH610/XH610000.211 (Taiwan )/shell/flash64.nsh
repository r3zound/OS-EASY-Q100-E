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
echo "2nd"
AfuEfix64.efi XH610000.211.bin /p /b /n /r
if not %lasterror% == 0 then
goto end
endif

copy ..\times.txt ..\twice.txt
FlashEC64.NSH 

:end
echo "  "
echo "Update not sucessful."
echo "  "

cd ..