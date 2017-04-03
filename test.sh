python fireball.py &
sleep 1
tail -f /opt/fireball/fireball.log &
curl -i -X POST --data-binary "@test.json" -H "Content-Type: application/json" http://localhost:5000/pdf