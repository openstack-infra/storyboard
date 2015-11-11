#!/usr/bin/env bash
if [ -f /usr/bin/apt-get ] ; then
    export DEBIAN_FRONTEND=noninteractive
    sudo apt-get install -y -q mysql-server libmysqlclient-dev python-dev
else
    sudo yum install -y mysql-server mysql python-devel
fi

# export default vars if not defined, to be available in conf file
export DB_USER=${DB_USER:-openstack_citest}
export DB_PASSWORD=${DB_PASSWORD:-openstack_citest}
export DB_TEST=${DB_TEST:-storyboard_test}

# create the user if needed
if [ $CREATE_USER ]; then
    if [ $DB_ADMIN_PASSWORD ]; then
        FLAG_PASS="-p$DB_ADMIN_PASSWORD"
    else
        FLAG_PASS=""
    fi
    mysql -u $DB_ADMIN_USER $FLAG_PASS -e "CREATE USER $DB_USER@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    mysql -u $DB_ADMIN_USER $FLAG_PASS -e "GRANT ALL PRIVILEGES ON $DB_TEST.* TO $DB_USER@'localhost';"
    mysql -u $DB_ADMIN_USER $FLAG_PASS -e "FLUSH PRIVILEGES;"
fi

# create the test database
mysql -u $DB_USER -p$DB_PASSWORD -e "DROP DATABASE IF EXISTS $DB_TEST;"
mysql -u $DB_USER -p$DB_PASSWORD -e "CREATE DATABASE $DB_TEST;"

# replace env vars
cd ${STORYBOARD_PATH:-storyboard}
sed -i -e "s/#DB_USER#/$DB_USER/g" -e "s/#DB_PASSWORD#/$DB_PASSWORD/g" -e "s/#DB_TEST#/$DB_TEST/g" ./etc/storyboard.conf.test
tox -e venv "storyboard-db-manage --config-file ./etc/storyboard.conf.test upgrade head"
tox -e venv "storyboard-api --config-file ./etc/storyboard.conf.test" &
