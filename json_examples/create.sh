#!/bin/bash

PORT=8080

clear
echo -e "Get auth token"
auth_token=$(curl -s -X GET http://localhost:${PORT}/token --user alforbes:moreblabla | json_pp | grep token | cut -d '"' -f 4) &>/dev/null
curl -vs -X GET http://localhost:${PORT}/token --user alforbes:moreblabla 
echo
read -n1 -p 'Press any key to continue'

clear
echo "Create release"
ril=$(curl -sv -H "X-Auth-Token: $auth_token" -H "Content-Type: application/json" -X POST "http://127.0.0.1:${PORT}/releases" -d @./releases.json | grep 'id' | cut -d '"' -f 4)
echo -e "Created release ${ril}\n\n"
read -n1 -p 'Press any key to continue'


clear
echo "Create package"
curl -sv -H "X-Auth-Token: $auth_token" -H "Content-Type: application/json" -X POST "http://127.0.0.1:${PORT}/releases/${ril}/packages" -d @./package.json
echo -e "Created package\n\n"
read -n1 -p 'Press any key to continue'


clear
echo "Start deploy"
curl -svH "X-Auth-Token: $auth_token" -v -X POST "http://127.0.0.1:${PORT}/releases/${ril}/deploy"; echo -e


read -n1 -p 'Press any key to continue'
clear
curl -svH "X-Auth-Token: $auth_token" -v -X GET "http://127.0.0.1:${PORT}/releases/${ril}" | jq .; echo -e
echo -e "Done"
