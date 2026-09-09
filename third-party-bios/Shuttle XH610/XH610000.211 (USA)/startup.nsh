#
# 
#
echo -off
###################### Info ###########################
cls
ver
date
time
echo "  "

#######################################################
#set env1 "world"
for %i in 0 1 2 3 4 5 6 7 8 9 A B C D E F
	if exist FS%i:\shell\flash64.nsh then
		#
		# Found location
		#
		goto start
	else
		goto end
	endif
	
	:start
FS%i:
				time >> times.txt
                                   # Due to update PK need to flash twice.
                                   if exist twice.txt then 
                                      rm once.txt
                                      rm twice.txt
                                      #goto complete
					goto once
                                   else
                                          if exist once.txt then
                                                     echo "   "
                                          else
:once
                                          	echo "    "
                                          	echo This BIOS needs to flash and reboot twice, it may take for a while.
                                          	echo During flashing BIOS, please do not power off the machine.
                                          	echo "    "   
                                          	pause

			cd shell
			flash1.nsh
			goto end
                                          endif

                                   endif

:twice
		#
		# Modify here
		#
			cd shell
			flash64.nsh
                                                                                                         
			goto end
		#
		# Complete
		#
		:complete
		echo "Flash complete."
			goto end
		#
		# End
		#
		:end
	
endfor

echo -on

#######################################################
#if %1 == '' then	#external variable
#endif
#######################################################