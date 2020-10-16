
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller
from mininet.node import OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import sys

# To test the network, run command (from same directory):
# sudo mn --custom ./Clos.py --topo Clos,k,n --test pingall
class Clos(Topo):

    CoreSwitchList = []
    AggSwitchList = []
    EdgeSwitchList = []
    Hosts = []

    def __init__(self, k, host_per_switch):
        self.pods = k
        self.nCoreSwitch = (k // 2)**2
        self.nAggSwitch = k**2 // 2
        self.nEdgeSwitch = k**2 // 2
        self.host_per_switch = host_per_switch
        self.nHosts = self.nEdgeSwitch * host_per_switch
        self.netRates = {'host_edge_bw': 1, 'edge_agg_bw': 1, 'agg_core_bw': 1}

        Topo.__init__(self) # , switch=OVSSwitch)
        
        self.addNodes()
        self.addLinks()


    def addNodes(self):
        self.addCoreNodes()
        self.addAggNodes()
        self.addEdgeNodes()
        self.addHosts()


    def addCoreNodes(self):
        for i in range(1, self.nCoreSwitch + 1):
            name = 's1'
            self.CoreSwitchList.append(self.addSwitch(name + str(i)))

    def addAggNodes(self):
        for i in range(1, self.nAggSwitch + 1):
            name = 's2'
            self.AggSwitchList.append(self.addSwitch(name + str(i)))

    def addEdgeNodes(self):
        for i in range(1, self.nEdgeSwitch + 1):
            name = 's3'
            self.EdgeSwitchList.append(self.addSwitch(name + str(i)))

    def addHosts(self):
        for i in range(1, self.nHosts+1):
            self.Hosts.append(self.addHost('h' + str(i)))

    def addLinks(self):
        size = self.pods // 2
        #Add core to aggregate switches. Each aggregate switch is connected to k/2 core
            #switches.
        for x in range(0, self.nAggSwitch, size):
            for i in range(0, size):
                for j in range(0, size):
                    options = dict(bw=self.netRates['agg_core_bw'])
                    self.addLink(
                            self.CoreSwitchList[i * size + j],
                            self.AggSwitchList[x + i],
                            **options
                            )

        #Connect aggregate to edge switches. Each edge switch is connected to k/2 aggregate switches.
        for x in range(0, self.nAggSwitch, size):
            for i in range(0, size):
                for j in range(0, size):
                    options = dict(bw=self.netRates['edge_agg_bw'])
                    self.addLink(
                        self.AggSwitchList[x + i],
                        self.EdgeSwitchList[x + j],
                        **options
                        )

        #Split up hosts and attach to edge switches
        for i in range(0, self.nEdgeSwitch):
            for j in range(0, self.host_per_switch):
                options = dict(bw=self.netRates['host_edge_bw'])
                self.addLink(
                    self.EdgeSwitchList[i],
                    self.Hosts[i * self.host_per_switch + j],
                    **options
                    )

topos = {'Clos': (lambda k, n: Clos(k, n))}

#Create a network
def createClos(k, n):
    topo = Clos(k, n)
    net = Mininet(topo=topo, controller=Controller)
    # net.addController('c0')
    net.start()
    CLI(net)
    net.stop()
    


if __name__ == '__main__':
    k = sys.argv[1]
    n = sys.argv[2]
    setLogLevel('info')
    createClos(int(k), int(n))
