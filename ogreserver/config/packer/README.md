Packer for ogreserver
=====================

Preamble
--------

Packer is a build tool for creating machine images. See [http://packer.io](http://packer.io).

In `ogreserver`, there is packer configuration for creating a production Amazon AMI for deployment on AWS, and a production Vagrant VM for pre-production testing.


Files
-----

The files in this directory are as follows:

  - `wheezy77.json`: Packer configuration for AMI and Vagrant builds.
  - `preseed.cfg`: Debian installer preseed file to automate Debian setup.
  - `scripts/*.sh`: Build scripts for bootstrapping Debian from the raw ISO state.
  - `salt-minion-packer.conf`: Salt-minion configuration for production Packer builds. This is applied to the machine image before Salt is run.
  - `build-vagrant.sh`: build a Vagrant box using Packer and add it as `ogreserver-packer` to local Vagrant boxes.
  - `Vagrantfile`: Vagrant config file used for testing prod builds.
  - `salt-minion-vagrant.conf`: Salt-minion configuration used for testing production builds in Vagrant. This applied when calling `vagrant up` after building a new box.


Build Workflow
--------------

A **pre-production** workflow is as follows:

1. Build a production Vagrant box using the packaged script.
2. Spin up the newly built Vagrant box locally.
3. Check everything appears correct! At this point, config management has successfully passed, and so have unit tests.

    ```
    ./build-vagrant.sh
    vagrant up
    ```

A **production** workflow is as follows:

1. Test the build according to pre-production rules.
2. Use packer command to build a new AMI on EC2.
3. Use salt-cloud to deploy this new AMI.

    ```
    ./build-production.sh
    ```


Credit
------

Much of the configuration in this directory is lifted from [mafrosis/packer-templates](https://github.com/mafrosis/packer-templates), and before that the projects listed there.
