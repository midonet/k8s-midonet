Kubernetes deployment guide on Multi Ubuntu nodes
=================================================

MidoNet requries Ubuntu (>= 14.04) to run. This documentation describes about
how to deploy K8s cluster on multiple plain Ubuntu nodes.

Prerequisites
-------------

* Ubuntu 14.04 LTS nodes, bare metal servers or VM instances, **where** Docker_ **is installed**
* Kubernetes master branch
* SSH accessibility **with the private IPs** from your computer to nodes where the
  cluster is deployed

  - You need to ssh into nodes beforehand
  - Generate ssh public key and add it to ``${HOME}/.ssh/authorized_keys`` on every ndoe

To make it short, please execute the following commands.

::

  $ sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
  $ sudo sh -c 'echo deb https://apt.dockerproject.org/repo ubuntu-trusty main >> /etc/apt/sources.list.d/docker.list'
  $ sudo apt-get update && sudo apt-get install -y git docker-engine
  $ git clone https://github.com/kubernetes/kubernetes.git
  $ cd kubernetes/cluster

.. _Docker: https://docs.docker.com/engine/installation/linux/ubuntulinux/


Deployment
----------

Please define the following environment variables as they're described in the
`official doc`_

.. _`official doc`: https://github.com/kubernetes/kubernetes/blob/master/docs/getting-started-guides/ubuntu.md#configure-and-start-the-kubernetes-cluster

In the following configuration, ``10.240.0.8`` is a master and a worker.
``10.240.0.9`` is another worker. *Please change them based on your
envrironment*

  **NOTE:** On the cloud services such as AWS or GCE, ``10.240.0.8`` and
  ``10.240.0.9`` should be *the private IP addresses* reachable for each other
  rather than the public IP such as Elastic IPs or ephemeral pubilc IPs. This
  implies you need to proceed the deployment process on an instance of the
  cloud service. You may also need to allow etcd access for port ``4001`` and
  ``2379`` through the firewall or other networking configurations.

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

That's it. You should see the following output if the deployment is succeeed.

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

If something went wrong in the middle of the deployment or you want to destory
the cluster, run ``cluster/kube-down.sh`` with
``KUBERNETES_PROVIDER=ubuntu``. You need to make it sure the environment
variables are defined appropriately as they're described above.

::

  $ . ubuntu_env
  $ KUBERNETES_PROVIDER=ubuntu ./kube-down.sh
