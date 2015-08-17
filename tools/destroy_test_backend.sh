#!/bin/bash

# This script cleans up the testing database and stops storyboard API
echo 'Killing storyboard-api...'
killall storyboard-api

# export default vars if not defined, to be available in conf file
export DB_USER=${DB_USER:-openstack_citest}
export DB_PASSWORD=${DB_PASSWORD:-openstack_citest}
export DB_TEST=${DB_TEST:-storyboard_test}

mysql -u $DB_USER -p$DB_PASSWORD -e "DROP DATABASE IF EXISTS $DB_TEST;"
