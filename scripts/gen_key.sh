mkdir key_gen/$1
cd key_gen/$1
ssh-keygen -t rsa -b 4096 -f key_gen/github_id_rsa -C keith+klayersbot@keithrozario.com
openssl rand -base64 -out key_gen/secret.key 48
key=$(<key_gen/secret.key)
openssl aes-256-cbc -e -in key_gen/github_id_rsa -out key_gen/github_id_rsa.enc -k $key
openssl aes-256-cbc -d -in key_gen/github_id_rsa.enc -out key_gen/github_id_rsa.dec -k $key