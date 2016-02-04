#!/bin/bash
PORT=5000
auth_token=$(curl -s -X GET http://localhost:${PORT}/token --user alforbes:moreblabla | json_pp | grep token | cut -d '"' -f 4)
echo auth_token
ril=$(curl -s -H "X-Auth-Token: $auth_token" -H "Content-Type: application/json" -X POST "http://127.0.0.1:${PORT}/releases" -d @./releases.json | grep 'id' | cut -d '"' -f 4)
echo $ril
curl -s  -H "X-Auth-Token: $auth_token" -H "Content-Type: application/json" -X POST "http://127.0.0.1:${PORT}/releases/${ril}/packages" -d @./package.json

echo "Relase created: ${ril}"


curl -H "X-Auth-Token: $auth_token" -v -X POST "http://127.0.0.1:${PORT}/releases/${ril}/deploy"; echo
