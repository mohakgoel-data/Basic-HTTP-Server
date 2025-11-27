--- Test Script: HTTP Server from Scratch ---

Use this script to verify all core functional requirements.

SERVER_URL="http://localhost:8080"
echo "--- Starting HTTP Server Verification ---"

--- 1. Basic GET and Echo ---

echo "1. GET / (Root)"
curl -i $SERVER_URL/ | grep "HTTP/1.1"

echo "2. GET /echo (Success)"

The double quotes around the URL are necessary here due to the '&' and '?' characters

curl -i "$SERVER_URL/echo?message=Hello+World" | grep "Echoing"

echo "3. GET /echo (400 Bad Request - Missing param)"
curl -i $SERVER_URL/echo | grep "HTTP/1.1"

--- 4. POST (Create Item 1) ---

echo "4. POST /data (Create Item 1 - Expect 201 Created)"

Capture and check the response for the assigned ID

RESPONSE_4=$(curl -s -X POST $SERVER_URL/data 

-H "Content-Type: application/json" 

-d '{"name":"Initial Article","views":100}')
echo "$RESPONSE_4" | grep "id"

We assume the ID is 1 for subsequent tests

ID_TO_TEST=1

--- 5. GET All Data ---

echo "5. GET /data (Read All - Expect array containing ID 1)"
curl -i $SERVER_URL/data | grep "Article"

--- 6. GET Single Item ---

echo "6. GET /data/:id (Read ID 1 - Expect 200 OK)"
curl -i $SERVER_URL/data/$ID_TO_TEST | grep "views"

--- 7. PUT (Update Item 1) ---

echo "7. PUT /data/:id (Update ID 1 - Expect 200 OK)"
curl -i -X PUT $SERVER_URL/data/$ID_TO_TEST 

-H "Content-Type: application/json" 

-d '{"name":"Updated Article","views":500}' | grep "Updated"

--- 8. GET 404 Not Found ---

echo "8. GET /data/:id (404 Not Found - Missing ID 999)"
curl -i $SERVER_URL/data/999 | grep "404 Not Found"

echo "9. GET /nonexistent (404 Not Found - Missing Path)"
curl -i $SERVER_URL/nonexistent | grep "404 Not Found"

echo "--- Test Suite Complete ---"