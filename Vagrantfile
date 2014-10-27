VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "trusty64"
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"

  config.vm.network :forwarded_port, host_ip: '127.0.0.1', guest: 3306, host: 3306
  config.vm.network :forwarded_port, host_ip: '127.0.0.1', guest: 15672, host: 15672
  config.vm.network :forwarded_port, host_ip: '127.0.0.1', guest: 5672, host: 5672

  config.vm.provider "virtualbox" do |v|
    v.name = "storyboard_dev"
  end

  config.vm.provision "shell", path: "vagrant/bootstrap.sh"

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "vagrant/puppet/manifests"
    puppet.manifest_file  = "site.pp"
    puppet.options="--verbose --debug"
  end
end
