import os
from flask import Flask, Request, jsonify, request
from netaddr import *
import random

class MyRequest(Request):
    def __init__(self, environ, populate_request=True, shallow=False):
        if not environ.get('CONTENT_TYPE', ''):
            environ['CONTENT_TYPE'] = 'application/json'
        super(self.__class__, self).__init__(environ, populate_request, shallow)

app = Flask(__name__)
app.request_class = MyRequest

@app.route('/Plugin.Activate', methods=['POST'])
def plugin_activate():
    resp = {
        "Implements": ["NetworkDriver"]
    }
    return jsonify(resp)


_networks = {}

@app.route('/NetworkDriver.CreateNetwork', methods=['POST'])
def create_network():
    network = request.json
    network['cidr'] = IPNetwork('192.168.0.0/24')
    network['gateway'] = str(network['cidr'].iter_hosts().next())
    network['ips'] = IPSet(list(IPNetwork(network['cidr'])[10:-10]))
    network['endpoints'] = {}
    _networks[network['NetworkID']] = network

    return jsonify({})

def error(msg):
    return jsonify({
        'Err': msg,
    })

@app.route('/NetworkDriver.DeleteNetwork', methods=['POST'])
def delete_network():
    network_id = request.json['NetworkID']
    if network_id not in _networks:
        return error('Network %s not found' % network_id)

    del _networks[network_id]
    return jsonify({})

def generate_mac():
    mac = [ 0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

@app.route('/NetworkDriver.CreateEndpoint', methods=['POST'])
def create_endpoint():
    network = _networks[request.json['NetworkID']]
    endpoint_id = request.json['EndpointID']

    if network['ips'].size == 0:
        return error('no more IP address')

    # create endpoint
    ip = random.choice(list(network['ips']))
    network['ips'].remove(ip)

    endpoint = {
        'Interfaces': [
            {
                'ID': 0,    # eth0
                'Address': '%s/%d' % (ip, network['cidr'].prefixlen),
                'MacAddress': generate_mac(),
            },
        ]
    }
    network['endpoints'][endpoint_id] = endpoint

    resp = endpoint
    return jsonify(resp)

@app.route('/NetworkDriver.EndpointOperInfo', methods=['POST'])
def endpoint_oper_info():
    network = _networks[request.json['NetworkID']]
    endpoint_id = request.json['EndpointID']
    endpoint = network['endpoints'][endpoint_id]

    resp = {
        'Value': {
        }
    }
    return jsonify(resp)

def veth_names(key):
    max_len = 15

    return (
        ('vs-%s' % key)[:max_len],
        ('vd-%sp' % key)[:max_len]
    )

@app.route('/NetworkDriver.Join', methods=['POST'])
def join():
    network = _networks[request.json['NetworkID']]
    endpoint = network['endpoints'][request.json['EndpointID']]
    sandbox_key = os.path.basename(request.json['SandboxKey'])
    endpoint['sandbox_key'] = sandbox_key

    veth, veth_peer = veth_names(sandbox_key)

    cmd = 'sudo ip link add %s type veth peer name %s' % (veth, veth_peer)
    os.system(cmd)

    resp = {
        'InterfaceNames': [
            {
                'SrcName': veth_peer,
                'DstPrefix': 'eth',
            },
        ],
        'Gateway': network['gateway'],
    }
    return jsonify(resp)

@app.route('/NetworkDriver.Leave', methods=['POST'])
def leave():
    network = _networks[request.json['NetworkID']]
    endpoint = network['endpoints'][request.json['EndpointID']]
    del network['endpoints'][request.json['EndpointID']]

    veth, veth_peer = veth_names(endpoint['sandbox_key'])

    os.system('sudo ip link del %s' % veth)

    for intf in endpoint['Interfaces']:
        network['ips'].add(intf['Address'])

    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)

