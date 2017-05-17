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
    echo 'en_GB.UTF-8 UTF-8' | tee -a /etc/locale.gen
    sudo localedef -i en_GB -f UTF-8 en_GB.UTF-8
    sudo locale-gen en_GB.UTF-8
    sudo sed -i 's/us.archive.ubuntu.com/nl.archive.ubuntu.com/g' /etc/apt/sources.list
#     sudo sed -i 's/us.archive.ubuntu.com/repositories.ecg.so/g' /etc/apt/sources.list
#     sudo sed -i 's/httpredir.debian.org/repositories.ecg.so/g' /etc/apt/sources.list

    sudo apt-get -qq update

    # Build/test tools
    apt-get -y install \
      build-essential \
      debhelper \
      dh-systemd \
      git-buildpackage \
      postgresql-client \
      libpq-dev \
      mysql-client \
      postgresql-server-dev-all \
      python-all-dev \
      python-dev \
      python-pip \
      python-stdeb \
      python-virtualenv \
      python3-all-dev \
      python3-dev \
      python3-pip \
      python3-stdeb \
      python3-virtualenv \
      python3-dev \
      vim \

    # python-ldap dependencies
    apt-get install -y \
      python-dev \
      libldap2-dev \
      libsasl2-dev \
      libssl-dev \

    sudo pip install --upgrade pip setuptools
    sudo pip install --upgrade stdeb virtualenv

    wget -P /tmp/ \
        'http://launchpadlibrarian.net/291737817/dh-virtualenv_1.0-1_all.deb'
    dpkg -i /tmp/dh-virtualenv_1.0-1_all.deb
    apt-get -f install -y

    # Setup a virtualenv; avoids conflicts, particularly with python-six
    virtualenv /home/vagrant/virtualenv/orlo_py27 --python=python2.7
    virtualenv /home/vagrant/virtualenv/orlo_py34 --python=python3.4

    source /home/vagrant/virtualenv/orlo_py34/bin/activate
    echo "source ~/virtualenv/orlo_py34/bin/activate" >> /home/vagrant/.profile

    pip install --upgrade pip setuptools

    cd /vagrant/orlo
    pip install .[test]
    pip install .[doc]
    python setup.py develop

    mkdir -p /etc/orlo /var/log/orlo
    chown -R vagrant:vagrant /var/log/orlo
    # echo -e "[db]\nuri=postgres://orlo:password@192.168.57.100" > /etc/orlo/orlo.ini


    chown -R vagrant:root /etc/orlo /var/log/orlo
    chown -R vagrant:vagrant /home/vagrant/virtualenv
    chown vagrant:root /vagrant
  SHELL

  config.vm.define "jessie" do |jessie|
    jessie.vm.box = "bento/debian-8.7"
    jessie.vm.network "forwarded_port", guest: 5000, host: 5100
    jessie.vm.network "private_network", ip: "192.168.57.20"
    jessie.vm.provision "shell", inline: <<-SHELL
    SHELL
  end

  config.vm.define "xenial" do |xenial|
    xenial.vm.box = "bento/ubuntu-16.04"
    xenial.vm.network "forwarded_port", guest: 5000, host: 5200
    xenial.vm.network "private_network", ip: "192.168.57.30"
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
      echo "host    all             all             192.168.57.0/24         md5" >> /etc/postgresql/9.5/main/pg_hba.conf
      sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/9.5/main/postgresql.conf
      systemctl restart postgresql.service
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
