Kubernetes and MidoNet deployment guide on Multi Ubuntu nodes
=============================================================

MidoNet requries Ubuntu (>= 14.04) to run. Howerver, the default multi node
cluster deployment script of k8s is targeted to Debian. This documentation
describes how to deploy k8s cluster with MidoNet on multiple plain Ubuntu
nodes.

This documentation doesn't cover the installation of MidoNet cluster. Please
consult with the official `quick start guide`_ and the `installation guide`_
for the MidoNet installation.

.. _`quick start guide`: https://www.midonet.org/#quickstart
.. _`installation guide`: https://docs.midonet.org/docs/latest-en/quick-start-guide/ubuntu-1404_liberty/content/_midonet_installation.html

Prerequisites
-------------

Please read the `official doc`_, especially its "`Prerequisites`_" section
first. You need a master node and worker nodes where the k8s cluster is
installed, and your computer from which you deploy the cluster copying the
necessary binaries over the cluster nodes. It can be the master or one of the
worker nodes.

* Ubuntu 14.04 LTS nodes, bare metal servers or VM instances, the master node and
  the worker ndoes **where** Docker_ **is installed**

  - For the MidoNet integration a MidoNet agent shall be installed on each
    worker, so at least 4GB RAM for each worker node is recommended

* Kubernetes master branch on your deployment node
* SSH accessibility **with the private IPs** from your computer to nodes where the
  cluster is deployed

  - You need to generate the ssh public key and add it to
    ``${HOME}/.ssh/authorized_keys`` on every node
  - You need to ssh into nodes beforehand

To make it short, please execute the following commands on *each worker node* to install all dependencies.

::

  $ sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
  $ sudo sh -c 'echo deb https://apt.dockerproject.org/repo ubuntu-trusty main >> /etc/apt/sources.list.d/docker.list'
  $ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 0x86F44E2A
  $ sudo sh -c 'echo deb http://ppa.launchpad.net/openjdk-r/ppa/ubuntu trusty main >> /etc/apt/sources.list.d/openjdk-8.list'
  $ sudo sh -c 'cat > /etc/apt/sources.list.d/midonet.list <<EOF
  # MidoNet
  deb http://builds.midonet.org/midonet-5 stable main

  # MidoNet OpenStack Integration
  deb http://builds.midonet.org/openstack-liberty stable main

  # MidoNet 3rd Party Tools and Libraries
  deb http://builds.midonet.org/misc stable main
  EOF'
  $ curl -L https://builds.midonet.org/midorepo.key | sudo apt-key add -
  $ sudo apt-get update && sudo apt-get install -y docker-engine openjdk-8-jre-headless midolman

After installing the dependencies, please make it sure you added your host to
the appropriate tunnel zone as described in `MidoNet Host Registration`_ section
of the official doc.

And then, please clone the k8s master branch on your computer as follow.

::

  $ sudo apt-get update && sudo apt-get install -y curl git
  $ git clone https://github.com/kubernetes/kubernetes.git
  $ cd kubernetes/cluster

.. _Prerequisites: https://github.com/kubernetes/kubernetes/blob/master/docs/getting-started-guides/ubuntu.md#prerequisites
.. _Docker: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _`MidoNet Host Registration`: https://docs.midonet.org/docs/latest-en/quick-start-guide/ubuntu-1404_liberty/content/_midonet_host_registration.html

Deployment
----------

Please define the following environment variables as they're described in the
`official doc`_.

.. _`official doc`: https://github.com/kubernetes/kubernetes/blob/master/docs/getting-started-guides/ubuntu.md#configure-and-start-the-kubernetes-cluster

In the following configuration, ``10.240.0.8`` is a master and a worker.
``10.240.0.9`` is another worker. *Please change them based on your
envrironment.*

  **NOTE:** On the cloud services such as AWS or GCP, ``10.240.0.8`` and
  ``10.240.0.9`` should be *the private IP addresses* reachable for each other
  rather than the public IP such as Elastic IPs or ephemeral public IPs. This
  implies you need to proceed the deployment process on an instance of the
  cloud service. You may also need to allow etcd access for port ``4001`` and
  ``2379`` through the firewall or other networking configurations. In order to
  do that, please consult with the documentations of `AWS`_ or `GCP`_.

.. _AWS: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html
.. _GCP: https://cloud.google.com/compute/docs/networks-and-firewalls#firewalls

::

  $ cat ubuntu_env
  export nodes="10.240.0.8 10.240.0.9"
  export role="ai i"
  export NUM_NODES=${NUM_NODES:-2}
  export SERVICE_CLUSTER_IP_RANGE=192.168.3.0/24
  export FLANNEL_NET=172.16.0.0/16
  $ . ubuntu_env

Then run ``cluster/kube-up.sh`` with ``KUBERNETES_PROVIDER=ubuntu``.

::

  $ KUBERNETES_PROVIDER=ubuntu ./kube-up.sh

That's it. You should see the following output if the deployment succeeded.

::

  Validate output:
  NAME                 STATUS    MESSAGE              ERROR
  controller-manager   Healthy   ok                   nil
  scheduler            Healthy   ok                   nil
  etcd-0               Healthy   {"health": "true"}   nil
  Cluster validation succeeded
  Done, listing cluster services:

  Kubernetes master is running at http://10.240.0.8:8080

Cleanup
-------

If something went wrong in the middle of the deployment or you want to destroy
the cluster, run ``cluster/kube-down.sh`` with
``KUBERNETES_PROVIDER=ubuntu``. You need to make sure the environment
variables are defined appropriately as they're described above.

::

  $ . ubuntu_env
  $ KUBERNETES_PROVIDER=ubuntu ./kube-down.sh
