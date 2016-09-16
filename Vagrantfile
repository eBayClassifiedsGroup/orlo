# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # config.vm.box = "ubuntu/trusty64"
  # config.vm.box_check_update = false

  config.vm.synced_folder ".", "/vagrant/orlo",
     type: "virtualbox", create: "true", owner: "vagrant"

  config.vm.provider "virtualbox" do |vb|
    vb.cpus = "2"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
  SHELL

  config.vm.define "trusty" do |trusty|
    trusty.vm.box = "ubuntu/trusty64"
    trusty.vm.network "forwarded_port", guest: 5000, host: 5100
    trusty.vm.network "private_network", ip: "192.168.57.10"

    trusty.vm.provision "shell", inline: <<-SHELL
      # sudo sed -i 's/archive.ubuntu.com/nl.archive.ubuntu.com/g' /etc/apt/sources.list
      apt-get -y install python-pip python-dev

      # python-ldap dependencies
      apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev

      # Build/test tools
      apt-get -y install build-essential git-buildpackage debhelper python-dev \
          python3-dev dh-systemd python-virtualenv python-tox
      wget -P /tmp/ \
          'https://launchpad.net/ubuntu/+archive/primary/+files/dh-virtualenv_0.11-1_all.deb'
      dpkg -i /tmp/dh-virtualenv_0.11-1_all.deb
      apt-get -f install -y

      pip install --upgrade pip setuptools virtualenv

      # Virtualenv is to avoid conflict with Debian's python-six
      virtualenv /home/vagrant/virtualenv/orlo
      source /home/vagrant/virtualenv/orlo/bin/activate
      echo "source ~/virtualenv/orlo/bin/activate" >> /home/vagrant/.profile

      pip install -r /vagrant/orlo/requirements.txt
      pip install -r /vagrant/orlo/requirements_testing.txt
      pip install -r /vagrant/orlo/docs/requirements.txt

      sudo chown -R vagrant:vagrant /home/vagrant/virtualenv

      # Create the database
      cd /vagrant/orlo
      python create_db.py
      python setup.py develop
      mkdir /etc/orlo
      chown vagrant:root /etc/orlo
      chown vagrant:root /vagrant
    SHELL
  end

  config.vm.define "xenial" do |xenial|
    xenial.vm.box = "ubuntu/xenial64"
    xenial.vm.network "forwarded_port", guest: 5000, host: 5200
    xenial.vm.network "private_network", ip: "192.168.57.20"

    xenial.vm.provision "shell", inline: <<-SHELL
      # sudo sed -i 's/archive.ubuntu.com/nl.archive.ubuntu.com/g' /etc/apt/sources.list
      apt-get -y install python-pip python-dev

      # python-ldap dependencies
      apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev

      # Build/test tools
      apt-get -y install build-essential git-buildpackage debhelper python-dev \
          python3-dev dh-systemd python-virtualenv python-tox
      wget -P /tmp/ \
          'https://launchpad.net/ubuntu/+archive/primary/+files/dh-virtualenv_0.11-1_all.deb'
      dpkg -i /tmp/dh-virtualenv_0.11-1_all.deb
      apt-get -f install -y

      pip install --upgrade pip setuptools virtualenv

      # Virtualenv is to avoid conflict with Debian's python-six
      virtualenv /home/vagrant/virtualenv/orlo
      source /home/vagrant/virtualenv/orlo/bin/activate
      echo "source ~/virtualenv/orlo/bin/activate" >> /home/vagrant/.profile

      pip install -r /vagrant/orlo/requirements.txt
      pip install -r /vagrant/orlo/requirements_testing.txt
      pip install -r /vagrant/orlo/docs/requirements.txt

      sudo chown -R vagrant:vagrant /home/vagrant/virtualenv

      # Create the database
      cd /vagrant/orlo
      python create_db.py
      python setup.py develop
      mkdir /etc/orlo
      chown vagrant:root /etc/orlo
      chown vagrant:root /vagrant
    SHELL
  end

  config.vm.define "db" do |db|
    db.vm.box = "ubuntu/xenial64"
    db.vm.network "private_network", ip: "192.168.57.100"
    db.vm.provision "shell", inline: <<-SHELL
      # sudo sed -i 's/archive.ubuntu.com/nl.archive.ubuntu.com/g' /etc/apt/sources.list
      apt-get -y install postgresql postgresql-server-dev-all
      echo "CREATE USER orlo WITH PASSWORD 'password'; CREATE DATABASE orlo OWNER orlo; " \
          | sudo -u postgres -i psql
    SHELL
  end

end
