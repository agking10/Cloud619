import sys
sys.path.append("/root/Cloud619")
from dctopo import FatTreeTopo
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller, RemoteController
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

c0 = RemoteController('c0', ip='127.0.0.1', port=6633) 

def createNetwork(n):
    topo = FatTreeTopo(n)
    net = Mininet(topo=topo, controller=Controller)
    net.addController('c0')

    net.start()
    CLI(net)
    net.stop()

topos = {"ft": FatTreeTopo}

if __name__ == '__main__':
    n = sys.argv[1]
    setLogLevel('info')
    createNetwork(int(n))
