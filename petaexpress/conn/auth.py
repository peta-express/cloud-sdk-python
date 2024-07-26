# =========================================================================
# Copyright 2012-present RAKSmart, Inc.
# -------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========================================================================

import sys
import hmac
import base64
import datetime
from hashlib import sha1, sha256

try:
    import urllib.parse as urllib
    is_python3 = True
except:
    import urllib
    is_python3 = False

from past.builtins import basestring

from petaexpress.misc.json_tool import json_dump, json_load
from petaexpress.misc.utils import get_utf8_value, get_ts, base64_url_decode,\
    base64_url_encode

# List of query string arguments which should be signed
QSA_TO_SIGN = [
    "acl", "cors", "delete", "policy", "stats", "part_number", "uploads", "upload_id"
]

class HmacKeys(object):
    """ Key based Auth handler helper.
    """
    host = None
    qy_access_key_id = None
    qy_secret_access_key = None
    _hmac = None
    _hmac_256 = None

    def __init__(self, host, qy_access_key_id, qy_secret_access_key):
        self.host = host
        self.update_provider(qy_access_key_id, qy_secret_access_key)

    def update_provider(self, qy_access_key_id, qy_secret_access_key):
        self.qy_access_key_id = qy_access_key_id
        self.qy_secret_access_key = qy_secret_access_key
        if is_python3:
            qy_secret_access_key = qy_secret_access_key.encode()
        self._hmac = hmac.new(qy_secret_access_key, digestmod=sha1)
        if sha256:
            self._hmac_256 = hmac.new(qy_secret_access_key, digestmod=sha256)
        else:
            self._hmac_256 = None

    def algorithm(self):
        if self._hmac_256:
            return 'HmacSHA256'
        else:
            return 'HmacSHA1'

    def digest(self, string_to_digest):
        if self._hmac_256:
            _hmac = self._hmac_256.copy()
        else:
            _hmac = self._hmac.copy()
        if is_python3:
            string_to_digest = string_to_digest.encode()
        _hmac.update(string_to_digest)
        return _hmac.digest()

    def sign_string(self, string_to_sign):
        to_sign = self.digest(string_to_sign)
        return base64.b64encode(to_sign).strip()


class QuerySignatureAuthHandler(HmacKeys):
    """ Provides Query Signature Authentication.
    """

    SignatureVersion = 1
    APIVersion = 1

    def _calc_signature(self, params, verb, path):
        """ calc signature for request
        """
        string_to_sign = '%s\n%s\n' % (verb, path)
        params['signature_method'] = self.algorithm()
        keys = sorted(params.keys())
        pairs = []
        for key in keys:
            val = get_utf8_value(params[key])
            if is_python3:
                key = key.encode()
            pairs.append(urllib.quote(key, safe='') + '=' +
                         urllib.quote(val, safe='-_~'))
        qs = '&'.join(pairs)
        string_to_sign += qs
        # print "string to sign:[%s]" % string_to_sign
        b64 = self.sign_string(string_to_sign)
        return (qs, b64)

    def add_auth(self, req, **kwargs):
        """ add authorize information for request
        """
        req.params['access_key_id'] = self.qy_access_key_id if 'access_key' not in kwargs else kwargs.get('access_key')
        if 'token' in kwargs:
            req.params['token'] = kwargs.get('token')
        req.params['signature_version'] = self.SignatureVersion if 'signature_version' not in kwargs \
            else kwargs.get('signature_version')
        req.params['version'] = self.APIVersion
        time_stamp = get_ts()
        req.params['time_stamp'] = time_stamp
        qs, signature = self._calc_signature(req.params, req.method,
                                             req.auth_path)
        # print 'query_string: %s Signature: %s' % (qs, signature)
        if req.method == 'POST':
            # req and retried req should not have signature
            params = req.params.copy()
            params["signature"] = signature
            req.body = urllib.urlencode(params)
            req.header = {
                'Content-Length': str(len(req.body)),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
                'Connection': 'Keep-Alive'
            }
        else:
            req.body = ''
            # if this is a retried req, the qs from the previous try will
            # already be there, we need to get rid of that and rebuild it
            req.params["signature"] = signature
            req.path = req.path.split('?')[0]
            req.path = (req.path + '?' + qs +
                        '&signature=' + urllib.quote_plus(signature))


class AppSignatureAuthHandler(QuerySignatureAuthHandler):
    """ Provides App Signature Authentication.
    """

    def __init__(self, app_id, secret_app_key, access_token=None):

        HmacKeys.__init__(self, "", app_id, secret_app_key)
        self.app_id = app_id
        self.access_token = access_token

    def sign_string(self, string_to_sign):

        to_sign = self.digest(string_to_sign)
        return base64_url_encode(to_sign)

    def extract_payload(self, payload, signature):

        expected_sig = self.sign_string(payload)
        if signature != expected_sig:
            return None

        return json_load(base64_url_decode(payload))

    def create_auth(self, access_info):
        """
        @param access_info: {user_id, access_token, action, zone, expires}
        @return {"payload":..., "signature": ...}
        """

        if "expires" not in access_info or not access_info["expires"]:
            raise Exception("expires must exist in access_info")

        payload = base64_url_encode(json_dump(access_info))
        signature = self.sign_string(payload)
        return {"payload": payload,
                "signature": signature}

    def add_auth(self, req, **kwargs):
        """ add authorize information for request
        """
        req.params['app_id'] = self.app_id
        if self.access_token:
            req.params['access_token'] = self.access_token
        req.params['signature_version'] = self.SignatureVersion
        req.params['version'] = self.APIVersion
        time_stamp = get_ts()
        req.params['time_stamp'] = time_stamp
        qs, signature = self._calc_signature(req.params, req.method,
                                             req.auth_path)
        # print 'query_string: %s Signature: %s' % (qs, signature)
        if req.method == 'POST':
            # req and retried req should not have signature
            params = req.params.copy()
            params["signature"] = signature
            req.body = urllib.urlencode(params)
            req.header = {
                'Content-Length': str(len(req.body)),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
                'Connection': 'Keep-Alive'
            }
        else:
            req.body = ''
            # if this is a retried req, the qs from the previous try will
            # already be there, we need to get rid of that and rebuild it
            req.path = req.path.split('?')[0]
            req.path = (req.path + '?' + qs +
                        '&signature=' + signature)


class QSSignatureAuthHandler(HmacKeys):

    def _parse_parameters(self, params):

        if isinstance(params, dict):
            return params.items()
        elif isinstance(params, basestring):
            args = []
            for param in params.split("&"):
                pairs = param.split("=")
                if len(pairs) == 1:
                    args.append((param, None))
                elif len(pairs) == 2:
                    args.append(pairs)
            return args
        else:
            return params

    def _generate_signature(self, method, auth_path, params, headers):

        params = self._parse_parameters(params)

        string_to_sign = "%s\n%s\n%s" % (method.upper(),
                                         headers.get("Content-MD5", ""),
                                         headers.get("Content-Type", ""))

        # Append request time string
        date_str = headers.get("Date", "")
        string_to_sign += "\n%s" % date_str

        # Generate signed headers
        signed_headers = filter(
            lambda x: x.lower().startswith("x-qs-"), headers.keys()
        )
        for header in sorted(signed_headers):
            string_to_sign += "\n%s:%s" % (header.lower(), headers[header])

        # Generate canonicalized query
        param_parts = []
        for param, value in sorted(params, key=lambda x: x[0]):
            if param not in QSA_TO_SIGN:
                continue
            if value is None:
                param_parts.append(param)
            else:
                param_parts.append("%s=%s" % (param, value))
        canonicalized_query = "&".join(param_parts)

        # Generate canonicalized resource
        canonicalized_resource = auth_path
        if canonicalized_query:
            canonicalized_resource += "?%s" % canonicalized_query

        string_to_sign += "\n%s" % canonicalized_resource

        signature = self.sign_string(string_to_sign)

        if sys.version > "3" and isinstance(signature, bytes):
            signature = signature.decode()

        return signature

    def get_auth(self, method, auth_path, params=None, headers=None):

        signature = self._generate_signature(method, auth_path,
                                             params or [], headers or {})

        return "QS %s:%s" % (self.qy_access_key_id, signature)

    def get_auth_parameters(self, method, auth_path, expires, params=None, headers=None):

        params = params or []

        auth_params = [
            ("X-QS-Algorithm", "QS-HMAC-SHA256"),
            ("X-QS-Credential", self.qy_access_key_id),
            ("X-QS-Date", datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")),
            ("X-QS-Expires", str(expires)),
        ]

        signature = self._generate_signature(method, auth_path,
                                             params + auth_params,
                                             headers or {})

        auth_params.append(("X-QS-Signature", signature))

        return dict(auth_params)

    def add_auth(self, req, **kwargs):
        if "auth_path" in kwargs:
            auth_path = kwargs["auth_path"]
        else:
            auth_path = req.auth_path
        signature = self._generate_signature(req.method, auth_path,
                                             req.params, req.header)
        req.header["Authorization"] = "QS %s:%s" % (self.qy_access_key_id,
                                                    signature)
