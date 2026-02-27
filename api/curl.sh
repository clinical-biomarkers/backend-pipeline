#PORT="8082"
PORT="4442"

ACCESS="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3MTA4MDYzOTMsIm5iZiI6MTcxMDgwNjM5MywianRpIjoiMmVlODc3ZjAtMmI4OS00YjZkLTg3MDctOWYwYTQ2ODkzZmI0IiwiZXhwIjoxNzEwODkyNzkzLCJpZGVudGl0eSI6Im15Z2x5Z2VuQGdtYWlsLmNvbSIsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyIsImNzcmYiOiI5MjhkZTE5Zi1jNGMwLTQ1MWYtYTk2Ni01NGYxMWY4Yzc5YjgifQ.vYyWFe5G1Qg-PHKIpbcaGIUmtfrbrSq28O6UIq8wFCY"
#curl -H "Content-Type: application/json" http://localhost:$PORT/auth/login/ -d '{"email": "myglygen@gmail.com", "password":"g1l2y3g4e5n!"}'


curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" http://localhost:$PORT/video/addnew/ -d '{"url":"https://www.youtube.com/embed/xyV5v5nRm6A?rel=0"}'


#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" http://localhost:$PORT/auth/userinfo/ -d '{"email": "myglygen@gmail.com"}'

#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" http://localhost:$PORT/auth/userupdate/ -d '{"email":"myglygen@gmail.com","access":"write", "status":1, "password":"g1l2y3g4e5n!"}'
#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" http://localhost:$PORT/auth/userdelete/ -d '{"email":"james.bond@gmail.com"}'

#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" http://localhost:$PORT/video/addnew/ -d '{"url":"https://www.youtube.com/embed/xyV5v5nRm6A?rel=0"}'

#curl -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS" http://localhost:$PORT/video/delete/ -d '{"id":"63d04393d634c7d21067b32e"}'

