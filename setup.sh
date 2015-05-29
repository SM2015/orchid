#!/bin/bash
mkdir /var/www
groupadd www
usermod -a -G www ec2-user
chown -R root:www /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} +
find /var/www -type f -exec chmod 0664 {} +
cd /var/www
sh -c "echo 'export ORCHID_AWS_SECRET_ACCESS_KEY=YOUR_DATA_HERE' >> ~/.bashrc"
sh -c "echo 'export ORCHID_AWS_ACCESS_KEY_ID=YOUR_DATA_HERE' >> ~/.bashrc"
sh -c "echo 'export AWS_STORAGE_BUCKET_NAME=YOUR_DATA_HERE' >> ~/.bashrc"
sh -c "echo 'export ORCHID_DATABASE_HOST=YOUR_DATA_HERE' >> ~/.bashrc"
sh -c "echo 'export ORCHID_DATABASE_NAME=YOUR_DATA_HERE' >> ~/.bashrc"
sh -c "echo 'export ORCHID_DATABASE_USERNAME=YOUR_DATA_HERE' >> ~/.bashrc"
sh -c "echo 'export ORCHID_DATABASE_PASSWORD=YOUR_DATA_HERE' >> ~/.bashrc"
source ~/.bashrc
#!/bin/bash -ex
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
#setup virtualenv
#mkvirtualenv orchid
git clone https://github.com/neuman/orchid.git
echo installing pip requirements...
pip install -r orchid/requirements.txt
echo installing bower requirements...
cd orchid
bower install --allow-root --config.interactive=false
#add the local_settings.py file
#start the server
echo starting the server...
python manage.py runserver 0.0.0.0:80
#gunicorn orchid.wsgi:application --bind 0.0.0.0:80
#start the celery daemon
echo starting celery...
python manage.py celery worker --loglevel=info








