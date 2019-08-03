mkdir $1
cd $1
ssh-keygen -t rsa -b 4096 -f ./github_id_rsa
openssl rand -base64 -out secret.key 48
openssl aes-256-cbc -e -in github_id_rsa -out github_id_rsa.enc -k file:./secret.key