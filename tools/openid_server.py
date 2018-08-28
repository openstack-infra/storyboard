# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import pecan
from pecan import request
from pecan import response
from pecan import rest

import openid.extensions.sreg
import openid.server.server
from openid.store.filestore import FileOpenIDStore

from wsgiref import simple_server


class controller(rest.RestController):
    _custom_actions = {
        "openid": ["GET", "POST"],
        "authorize_return": ["GET"],
        "token": ["POST"],
    }

    def __init__(self, data):
        self._data = data
        super(controller, self).__init__()

    @pecan.expose()
    def openid(self):
        store = FileOpenIDStore('/tmp')
        oserver = openid.server.server.Server(store, '/')
        oid_request = oserver.decodeRequest(request.params)
        if isinstance(oid_request, openid.server.server.CheckIDRequest):
            sreg_req = openid.extensions.sreg.SRegRequest.fromOpenIDRequest(
                oid_request)
            data = {}
            for field in sreg_req.required + sreg_req.optional:
                data[field] = self.data[field]
                sr_resp = openid.extensions.sreg.SRegResponse.extractResponse(
                    sreg_req, data)
                oid_response = oid_request.answer(
                    True, identity=self._data['identity'])
                oid_response.addExtension(sr_resp)
        elif isinstance(oid_request, openid.server.server.CheckAuthRequest):
            oid_response = oserver.openid_check_authentication(oid_request)
            pass
        webresponse = oserver.encodeResponse(oid_response)

        response.status_code = webresponse.code
        for k, v in webresponse.headers.items():
            response.headers[k] = v.encode('utf-8')
        response.body = webresponse.body.encode('utf-8')

        return response


def setup_app(data, pecan_config=None):
    app = pecan.make_app(
        controller(data),
        debug=True,
        guess_content_type_from_ext=False
    )

    return app


def start():
    parser = argparse.ArgumentParser(description='A simple OpenID Server.')
    parser.add_argument('fullname',
                        help='The full name to return in the response')
    parser.add_argument('email',
                        help='The email address to return in the response')
    parser.add_argument('identity',
                        help='The identity to return in the response')

    args = parser.parse_args()
    data = dict(fullname=args.fullname,
                email=args.email,
                identity=args.identity)

    api_root = setup_app(data)
    srv = simple_server.make_server('0.0.0.0', 8088, api_root)
    srv.serve_forever()

if __name__ == '__main__':
    start()
