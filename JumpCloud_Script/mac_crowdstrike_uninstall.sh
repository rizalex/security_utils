#!/usr/bin/env bash
# Joe Schlimmer
# Please run on JumpCloud using root permission
# Uninstall Crowdstrike Falcon sensor

ERROR=0

if [[ -f "/Applications/Falcon.app/Contents/Resources/falconctl" ]]; then
    echo "Falcon 6.x installed, removing"
    /Applications/Falcon.app/Contents/Resources/falconctl uninstall
elif [[ -f "/Library/CS/falconctl" ]]; then
    echo "Falcon 5.x installed, removing"
    /Library/CS/falconctl uninstall
else
    echo "Falcon sensor app not found"
    ERROR=1
fi

exit $ERROR
