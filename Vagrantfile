# -*- mode: ruby -*-
# vi: set ft=ruby ts=2 sw=2 expandtab :

Vagrant.configure(2) do |config|
  # config.vm.box = "ubuntu/trusty64"
  # config.vm.box_check_update = false

  config.vm.synced_folder ".", "/vagrant/orlo",
     type: "virtualbox", create: "true", owner: "vagrant"

  config.vm.provider "virtualbox" do |vb|
    vb.cpus = "2"
  end

  config.vm.provision "shell", inline: <<-SHELL
    sudo localedef -i en_GB -f UTF-8 en_GB.UTF-8
    sudo locale-gen en_GB.UTF-8
    # sudo sed -i 's/us.archive.ubuntu.com/nl.archive.ubuntu.com/g' /etc/apt/sources.list
    sudo sed -i 's/us.archive.ubuntu.com/repositories.ecg.so/g' /etc/apt/sources.list
    sudo sed -i 's/httpredir.debian.org/repositories.ecg.so/g' /etc/apt/sources.list

    sudo apt-get -qq update

    # Build/test tools
    apt-get -y install \
      build-essential \
      debhelper \
      dh-systemd \
      git-buildpackage \
      postgresql-server-dev-all \
      python-all-dev \
      python-dev \
      python-pip \
      python-stdeb \
      python-virtualenv
      python3-dev \
      vim \

    # python-ldap dependencies
    apt-get install -y \
      python-dev \
      libldap2-dev \
      libsasl2-dev \
      libssl-dev \

    mkdir /etc/orlo
    chown vagrant:root /etc/orlo
    chown vagrant:root /vagrant

    # Updating build tooling can help
    sudo pip install --upgrade \
      pip \
      setuptools \
      stdeb \
      virtualenv

    wget -P /tmp/ \
        'https://launchpad.net/ubuntu/+archive/primary/+files/dh-virtualenv_0.11-1_all.deb'
    dpkg -i /tmp/dh-virtualenv_0.11-1_all.deb
    apt-get -f install -y

    # Setup a virtualenv; avoids conflicts, particularly with python-six
    virtualenv /home/vagrant/virtualenv/orlo
    source /home/vagrant/virtualenv/orlo/bin/activate
    echo "source ~/virtualenv/orlo/bin/activate" >> /home/vagrant/.profile

    pip install -r /vagrant/orlo/requirements.txt
    pip install -r /vagrant/orlo/requirements_testing.txt
    pip install -r /vagrant/orlo/docs/requirements.txt

    sudo chown -R vagrant:vagrant /home/vagrant/virtualenv

  SHELL

  config.vm.define "jessie" do |jessie|
    jessie.vm.box = "bento/debian-8.5"
    jessie.vm.network "forwarded_port", guest: 5000, host: 5000
    jessie.vm.network "private_network", ip: "192.168.57.20"
    jessie.vm.provision "shell", inline: <<-SHELL
      # Create the database
      cd /vagrant/orlo
      python create_db.py
      python setup.py develop
      mkdir /etc/orlo
      chown vagrant:root /etc/orlo
      chown vagrant:root /vagrant
    SHELL
  end


  config.vm.define "trusty" do |trusty|
    trusty.vm.box = "bento/ubuntu-14.04"
    trusty.vm.network "forwarded_port", guest: 5000, host: 5100
    trusty.vm.network "private_network", ip: "192.168.57.10"

    trusty.vm.provision "shell", inline: <<-SHELL
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
    xenial.vm.box = "bento/ubuntu-16.04"
    xenial.vm.network "forwarded_port", guest: 5000, host: 5200
    xenial.vm.network "private_network", ip: "192.168.57.20"

    xenial.vm.provision "shell", inline: <<-SHELL
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
    db.vm.box = "bento/ubuntu-16.04"
    db.vm.network "forwarded_port", guest: 5000, host: 15432
    db.vm.network "forwarded_port", guest: 5000, host: 13306
    db.vm.network "private_network", ip: "192.168.57.100"

    # postgres
    db.vm.provision "shell", inline: <<-SHELL
      apt-get -y install postgresql postgresql-server-dev-all
      echo "CREATE USER orlo WITH PASSWORD 'password'; CREATE DATABASE orlo OWNER orlo; " \
          | sudo -u postgres -i psql

    SHELL
    # mysql
    db.vm.provision "shell", inline: <<-SHELL
      echo "mysql-server mysql-server/root_password password vagrant" | sudo debconf-set-selections
      echo "mysql-server mysql-server/root_password_again password vagrant" | sudo debconf-set-selections
      apt-get -y install mysql-server
      echo "create user 'orlo'@'*' identified by 'password'; CREATE DATABASE orlo; " \
        "GRANT ALL on orlo.* TO 'orlo'@'*';" | mysql -uroot -pvagrant
    SHELL
  end

end
