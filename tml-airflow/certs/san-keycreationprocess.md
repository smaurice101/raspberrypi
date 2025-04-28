## generate rootca private key
openssl genrsa  -out ca.key 4096

## generate rootCA certificate
openssl req -new -x509 -days 3650  -config san.cnf  -key ca.key -out ca.crt

## Verify the rootCA certificate content and X.509 extensions
openssl x509 -noout -text -in ca.crt

## Generate private key
openssl genrsa -out server.key 4096

## Generate CSR (certificate signing request) for SAN
openssl req -new -key server.key -out server.csr -config san.cnf

## View CSR
openssl req -noout -text -in server.csr | grep -A 1 "Subject Alternative Name"

## Generate SAN certificate
openssl x509 -req -days 3650 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

## Generate SAN with extensions
openssl x509 -req -days 3650 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -extensions req_ext -extfile san.cnf

# View SAN certificate
openssl x509 -text -noout -in server.crt | grep -A 1 "Subject Alternative Name"

#------------------------------------------------------------------------------
# Create Client key
openssl req -new -newkey rsa:4096 -keyout client.key -out client.csr -nodes -subj '/CN=TML Client'

## sign the client key
openssl x509 -req -days 36500 -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt
