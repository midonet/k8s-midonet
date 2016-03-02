# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import contextlib
import json
import logging
import os

from oslo_config import cfg
from oslo_service import service
import requests
import six

from raven.commons import config


K8S_API_ENDPOINT_BASE = config.CONF.k8s_api_root
K8S_API_ENDPOINT_V1 = K8S_API_ENDPOINT_BASE + '/api/v1'
LOG_FILENAME = 'watcher.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
LOG = logging.getLogger(__name__)


# Borrowed from https://github.com/kennethreitz/requests/issues/2433
def _iter_lines(fd, chunk_size=1024):
    """Iterates over the content of a file-like object line-by-line."""
    pending = None

    while True:
        chunk = os.read(fd.fileno(), chunk_size)
        if not chunk:
            break

        if pending is not None:
            chunk = pending + chunk
            pending = None

        lines = chunk.splitlines()

        if lines and lines[-1]:
            pending = lines.pop()

        for line in lines:
            yield line

    if pending:
        yield(pending)


@six.add_metaclass(abc.ABCMeta)
class K8sApiWatcher(service.Service):
    """A K8s API watcher service watches and translates K8s resources.

    ``K8sApiWatcher`` makes the GET requests against the MidoNet integration
    related K8s endpoints with ``?watch=true`` query string and receive a series
    of event notification on the watched resource endpoints. The even
    notifications are given in the JSON format. Then ``K8sApiWatcher`` translate
    the events into the creations, deletions or updates of Neutron resources.
    """
    # TODO(tfukushima): Initialize the global neutronclient here.
    neutorn = None

    def __init__(self):
        super(K8sApiWatcher, self).__init__()

    def restart(self):
        LOG.debug('Restarted the service: {0}'.format(self.__class__.__name__))

    def start(self):
        LOG.debug('Started the service: {0}'.format(self.__class__.__name__))
        self.watch()

    def stop(self):
        LOG.debug('Stopped the service: {0}'.format(self.__class__.__name__))

    def wait(self):
        LOG.debug('Wait for the service: {0}'.format(self.__class__.__name__))

    def watch(self):
        # http://docs.python-requests.org/en/master/user/advanced/#streaming-requests  # noqa
        with contextlib.closing(requests.get(self.WATCH_ENDPOINT,
                                             stream=True)) as r:
            response_stream = _iter_lines(r.raw)
            # The first line is the number of bytes read.
            for response in response_stream:
                try:
                    decoded_json = json.loads(response)
                except ValueError, e:
                    pass
                else:
                    # Only legitimate JSON data should be accepted.
                    # ``decoded_json`` can be a string.
                    if type(decoded_json) is dict:
                        self.translate(decoded_json)
        self.stop()

    @abc.abstractmethod
    def translate(self, decoded_json):
        """Translates an event notification from the apiserver.

        This method tranlates the piece of JSON response into requests against
        the Neutron API. Subclasses of ``K8sApiWatcher`` **must** implements
        this method to have the concrete translation logic for the specific
        one or more resources.

        :param decoded_json: the decoded JSON resopnse from the apiserver.
        """
        pass


class K8sPodsWatcher(K8sApiWatcher):
    """A Pod watcher.

    ``K8sPodsWatcher`` makes a GET requrest against ``/api/v1/pods?watch=true``
    and receives the event notifications. Then it translates them into
    requrests aginst the Neutron API.

    An example of a JSON response from the apiserver is following. It is
    pretty-printed but the actual response will be provided as a line of JSON.
    ::

      {
        "type": "ADDED",
        "object": {
          "kind": "Pod",
          "apiVersion": "v1",
          "metadata": {
            "name": "frontend-qr8d6",
            "generateName": "frontend-",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/pods/frontend-qr8d6",
            "uid": "8e174673-e03f-11e5-8c79-42010af00003",
            "resourceVersion": "107227",
            "creationTimestamp": "2016-03-02T06:25:27Z",
            "labels": {
              "app": "guestbook",
              "tier": "frontend"
            },
            "annotations": {
              "kubernetes.io/created-by": {
                "kind": "SerializedReference",
                "apiVersion": "v1",
                "reference": {
                  "kind": "ReplicationController",
                  "namespace": "default",
                  "name": "frontend",
                  "uid": "8e1657d9-e03f-11e5-8c79-42010af00003",
                  "apiVersion": "v1",
                  "resourceVersion": "107226"
                }
              }
            }
          },
          "spec": {
            "volumes": [
              {
                "name": "default-token-wpfjn",
                "secret": {
                  "secretName": "default-token-wpfjn"
                }
              }
            ],
            "containers": [
              {
                "name": "php-redis",
                "image": "gcr.io/google_samples/gb-frontend:v3",
                "ports": [
                  {
                    "containerPort": 80,
                    "protocol": "TCP"
                  }
                ],
                "env": [
                  {
                    "name": "GET_HOSTS_FROM",
                    "value": "dns"
                  }
                ],
                "resources": {
                  "requests": {
                    "cpu": "100m",
                    "memory": "100Mi"
                  }
                },
                "volumeMounts": [
                  {
                    "name": "default-token-wpfjn",
                    "readOnly": true,
                    "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount"
                  }
                ],
                "terminationMessagePath": "/dev/termination-log",
                "imagePullPolicy": "IfNotPresent"
              }
            ],
            "restartPolicy": "Always",
            "terminationGracePeriodSeconds": 30,
            "dnsPolicy": "ClusterFirst",
            "serviceAccountName": "default",
            "serviceAccount": "default",
            "securityContext": {}
          },
          "status": {
            "phase": "Pending"
          }
        }
      }
    """
    PODS_ENDPOINT = K8S_API_ENDPOINT_V1 + '/pods'
    WATCH_ENDPOINT = PODS_ENDPOINT + '?watch=true'

    def translate(self, decoded_json):
        LOG.debug("Pod notification {0}".format(decoded_json))


class K8sServicesWatcher(K8sApiWatcher):
    """A service watcher.

    ``K8sServicesWatcher`` makes a GET request against
    ``/api/v1/services?watch=true`` and receives the event notifications. Then
    it translates them into requrests against the Neutron API.

    An example of a JSON response is following. It is pretty-printed but the
    actual response will be provided as a line of JSON.
    ::
    
      {
        "type": "ADDED",
        "object": {
          "kind": "Service",
          "apiVersion": "v1",
          "metadata": {
            "name": "kubernetes",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/services/kubernetes",
            "uid": "7c8c674f-d6ed-11e5-8c79-42010af00003",
            "resourceVersion": "7",
            "creationTimestamp": "2016-02-19T09:45:18Z",
            "labels": {
              "component": "apiserver",
              "provider": "kubernetes"
            }
          },
          "spec": {
            "ports": [
              {
                "name": "https",
                "protocol": "TCP",
                "port": 443,
                "targetPort": 443
              }
            ],
            "clusterIP": "192.168.3.1",
            "type": "ClusterIP",
            "sessionAffinity": "None"
          },
          "status": {
            "loadBalancer": {}
          }
        }
      }
    """
    SERVICES_ENDPOINT = K8S_API_ENDPOINT_V1 + '/services'
    WATCH_ENDPOINT = SERVICES_ENDPOINT + '?watch=true'

    def translate(self, decoded_json):
        LOG.debug("Service notification {0}".format(decoded_json))


if __name__ == '__main__':
    pods_watcher = service.launch(config.CONF, K8sPodsWatcher(), workers=1)
    pods_watcher.wait()
