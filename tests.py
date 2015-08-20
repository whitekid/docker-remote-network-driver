#! -*- coding: utf8 -*-
import json
import unittest
import uuid

from app import app

class TestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.debug = True

    def post(self, url, *args, **kwargs):
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'])

        resp = self.client.post(url, *args, **kwargs)
        return json.loads(resp.data)

    def test_create_network(self):
        data = {
            'NetworkID': str(uuid.uuid4()),
            'Options': {},
        }
        resp = self.post('/NetworkDriver.CreateNetwork', data=data)
        self.assertEquals({}, resp)

    def create_network(self):
        network_id = str(uuid.uuid4())
        data = {
            'NetworkID': network_id,
            'Options': {},
        }
        self.post('/NetworkDriver.CreateNetwork', data=data)
        return network_id

    def test_create_endpoint(self):
        network_id = self.create_network()
        endpoint_id = str(uuid.uuid4())

        data = {
            'NetworkID': network_id,
            'EndpointID': endpoint_id,
            'Options': {},
            'Interfaces': [],
        }
        resp = self.post('/NetworkDriver.CreateEndpoint', data=data)
        self.assertIn('Interfaces', resp)
        for intf in resp['Interfaces']:
            self.assertIsNotNone(intf['ID'])
            self.assertIsNotNone(intf['Address'])
            self.assertIsNotNone(intf['MacAddress'])

    def create_endpoint(self, network_id):
        endpoint_id = str(uuid.uuid4())

        data = {
            'NetworkID': network_id,
            'EndpointID': endpoint_id,
            'Options': {},
            'Interfaces': [],
        }
        resp = self.post('/NetworkDriver.CreateEndpoint', data=data)
        return endpoint_id

    def test_join(self):
        network_id = self.create_network()
        endpoint_id = self.create_endpoint(network_id)

        data = {
            'NetworkID': network_id,
            'EndpointID': endpoint_id,
            'SandboxKey': 'sandbox',
            'Options': {},
        }
        resp = self.post('/NetworkDriver.Join', data=data)
        for intf_name in resp['InterfaceNames']:
            self.assertTrue(intf_name['SrcName'])
            self.assertIn('DstPrefix', intf_name)
        # resp['Gateway'] optional


if __name__ == '__main__':
    unittest.main()

