"""
Interface to QingStor (PetaExpress Object Storage).
"""

from petaexpress.qingstor.connection import QSConnection


def connect(host, access_key_id=None, secret_access_key=None):
    """ Connect to qingstor by access key.
    """
    return QSConnection(access_key_id, secret_access_key, host)
