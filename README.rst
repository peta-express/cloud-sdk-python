=====================
PetaExpress Python SDK
=====================

This repository allows you to access `PetaExpress <https://www.petaexpress.com>`_
and control your resources from your applications.

This SDK is licensed under
`Apache Licence, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`_.

.. note::
  Requires Python 2.6 or higher, compatible with Python 3,
  for more information please see
  `PetaExpress SDK Documentation <https://docs.petaexpress.com/sdk/>`_


------------
Installation
------------

Install via `pip <http://www.pip-installer.org>`_ ::

    $ pip install petaexpress-sdk

Upgrade to the latest version ::

    $ pip install --upgrade petaexpress-sdk

Install from source ::

    git clone https://github.com/raksmart/petaexpress-sdk-python.git
    cd petaexpress-sdk-python
    python setup.py install


---------------
Getting Started
---------------

In order to operate PetaExpress IaaS or QingStor (PetaExpress Object Storage),
you need apply **access key** on `petaexpress console <https://console.petaexpress.com>`_ first.


PetaExpress IaaS API
'''''''''''''''''''
1. Pass access key id and secret key into method ``connect_to_zone`` to create connection ::

      >>> import petaexpress.iaas
      >>> conn = petaexpress.iaas.connect_to_zone(
              'zone id',
              'access key id',
              'secret access key'
          )


2. Call API by using IAM role

If you would like to call our APIs without access key and secret key (bad things would happen if they were lost or leaked)
or if you want a finer access control over your instances, there is a easy way to do it :P

- Go to our IAM service, create an instance role and attach it to your instance.
- Create connection without access key and secret key. ::

      >>> import petaexpress.iaas
      >>> conn = petaexpress.iaas.connect_to_zone(
            'zone id',
             None,
             None
          )


The variable ``conn`` is the instance of ``petaexpress.iaas.connection.APIConnection``,
we can use it to call resource related methods. Example::

  # launch instances
  >>> ret = conn.run_instances(
          image_id='img-xxxxxxxx',
          cpu=1,
          memory=1024,
          vxnets=['vxnet-0'],
          login_mode='passwd',
          login_passwd='Passw0rd@()'
      )

  # stop instances
  >>> ret = conn.stop_instances(
          instances=['i-xxxxxxxx'],
          force=True
        )

  # describe instances
  >>> ret = conn.describe_instances(
          status=['running', 'stopped']
        )

PetaExpress QingStor API
'''''''''''''''''''''''
Pass access key id and secret key into method ``connect`` to create connection ::

  >>> import petaexpress.qingstor
  >>> conn = petaexpress.qingstor.connect(
          'pek3a.qingstor.com',
          'access key id',
          'secret access key'
      )

The variable ``conn`` is the instance of ``petaexpress.qingstor.connection.QSConnection``,
we can use it to create Bucket which is used for generating Key and MultiPartUpload.

Example::

  # Create a bucket
  >>> bucket = conn.create_bucket('mybucket')

  # Create a key
  >>> key = bucket.new_key('myobject')
  >>> with open('/tmp/myfile') as f:
  >>>     key.send_file(f)

  # Delete the key
  >>> bucket.delete_key('myobject')

