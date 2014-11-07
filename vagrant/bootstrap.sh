#!/bin/sh

apt-get update
apt-get install puppet

if [ ! -d "/etc/puppet/modules/mysql" ]; then
    puppet module install puppetlabs-mysql --version 0.6.1
fi

if [ ! -d "/etc/puppet/modules/rabbitmq" ]; then
    puppet module install puppetlabs-rabbitmq --version 4.1.0
fi

if [ ! -d "/etc/puppet/modules/erlang" ]; then
    puppet module install garethr-erlang --version 0.3.0
fi

