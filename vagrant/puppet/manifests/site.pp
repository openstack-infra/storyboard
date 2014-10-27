node default {
  $dev_user = 'storyboard'
  $dev_password = 'storyboard'

  include 'erlang'
  package { 'erlang-base':
    ensure => 'latest',
    before => Class['rabbitmq']
  }

  ##########################################################
  ##
  ## RabbitMQ
  ##
  class { 'rabbitmq':
    service_manage    => true,
    manage_repos      => false,
    delete_guest_user => true,
    default_user      => $dev_user,
    default_pass      => $dev_password,
  }

  rabbitmq_user { $dev_user:
    ensure   => present,
    admin    => true,
    password => $dev_password,
    require  => Class['rabbitmq']
  }

  rabbitmq_user_permissions { "${dev_user}@/":
    configure_permission => '.*',
    read_permission      => '.*',
    write_permission     => '.*',
    require              => Rabbitmq_user[$dev_user],
  }

  ##########################################################
  ##
  ## MySQL
  ##
  class {'mysql::server':
    config_hash => {
      bind_address => '0.0.0.0'
    }
  }

  mysql::db { 'storyboard':
    user     => $dev_user,
    password => $dev_password,
    host     => '%',
  }

  database_user{ 'openstack_citest@%':
    ensure        => present,
    password_hash => mysql_password('openstack_citest'),
    require       => Class['mysql::server'],
  }

  database_grant{ 'openstack_citest@%/storyboard\_test\_db\_%':
    privileges => ['ALL'],
    require    => Database_user['openstack_citest@%']
  }
}
