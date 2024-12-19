## generate rootca private key
openssl genrsa  -out cakey.pem 4096

## generate rootCA certificate
openssl req -new -x509 -days 3650  -config openssl.cnf  -key cakey.pem -out cacert.pem

## Verify the rootCA certificate content and X.509 extensions
openssl x509 -noout -text -in cacert.pem

## Generate private key
openssl genrsa -out server.key 4096

## Generate CSR (certificate signing request) for SAN
openssl req -new -key server.key -out server.csr -config san.cnf

## View CSR
openssl req -noout -text -in server.csr | grep -A 1 "Subject Alternative Name"

## Generate SAN certificate
openssl x509 -req -days 3650 -in server.csr -CA cacert.pem -CAkey cakey.pem -CAcreateserial -out server.crt

## Generate SAN with extensions
openssl x509 -req -days 3650 -in server.csr -CA cacert.pem -CAkey cakey.pem -CAcreateserial -out server.crt -extensions req_ext -extfile san.cnf

# View SAN certificate
openssl x509 -text -noout -in server.crt | grep -A 1 "Subject Alternative Name"

#------------------------------------------------------------------------------
# Create Client key
openssl req -new -newkey rsa:4096 -keyout client.key -out client.csr -nodes -subj '/CN=TML Client'

## sign the client key
openssl x509 -req -days 36500 -in client.csr -CA cacert.pem -CAkey cakey.pem -CAcreateserial -out client.crt
