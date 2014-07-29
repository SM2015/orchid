To deploy Project Orchid

Installation
------------

#!/bin/bash -ex
#cd /home/ubuntu
echo spinning up...
#install system programs
echo installing system programs...
apt-get update
apt-get -y install python-pip python2.7-dev git nodejs npm libpq-dev python-dev redis-server python-mysqldb libmysqlclient-dev
pip install virtualenvwrapper 
#link node if needed
echo linking virtualenv...
ln -s /usr/bin/nodejs /usr/bin/node
npm install -g --config.interactive=false bower
npm install --save --config.interactive=false bower-requirejs
#add variables to environment
#echo adding environment variables...
#sh -c "echo 'export WORKON_HOME=$HOME/.virtualenvs' >> ~/.bashrc"
#sh -c "echo 'export PROJECT_HOME=$HOME/directory-you-do-development-in' >> ~/.bashrc"
#sh -c "echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc"
#sh -c "echo 'export NODE_PATH=$HOME/local/lib/node_modules' >> ~/.bashrc"
exit
#reload
#bash --login 
#setup virtualenv
#mkvirtualenv orchid
git clone https://github.com/neuman/orchid.git
echo installing pip requirements...
pip install -r orchid/requirements.txt
echo installing bower requirements...
cd orchid
bower install --allow-root --config.interactive=false
#add the local_settings.py file
echo building local_settings file...
echo AWS_SECRET_ACCESS_KEY = '"INSERT KEY HERE"' >> orchid/local_settings.py
echo AWS_ACCESS_KEY_ID = '"INSERT KEY HERE"' >> orchid/local_settings.py
echo AWS_STORAGE_BUCKET_NAME = '"moh.tablet.test"' >> orchid/local_settings.py
#start the server
echo starting the server...
gunicorn orchid.wsgi:application --bind 0.0.0.0:80
#start the celery daemon
echo starting celery...
python manage.py celery worker --loglevel=info








