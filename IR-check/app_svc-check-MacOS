#!/bin/zsh

#applications check
system_profiler SPApplicationsDataType -xml >> info_app.xml
#sudo find / -iname *.app >> appinfo1.txt
ls /Applications >> info_app.txt

#services check
launchctl list >> info_svc.txt
ps aux >> info_svc1.txt


#How to use? (MacOS only)
# chmod +x app_svc-check
# sudo app_svc-check

# will produce file app_info.xml | info_app.txt | info_svc.txt | info_svc1.txt (just analyst it)
