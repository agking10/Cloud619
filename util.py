# utility functions
'''
based on pipl-pox
'''
from DCTopo import FatTreeTopo
from mininet.util import makeNumeric
from DCRouting import HashedRouting
from DCRouting import DijkstraRouting
from DCRouting import WeightedRouting


TOPOS = {'ft': FatTreeTopo}
ROUTING = {'WCMP' : WeightedRouting,  'ECMP' : HashedRouting, 'dij' : DijkstraRouting}


def buildTopo(topo):
    topo_name, topo_param = topo.split( ',' )
    return TOPOS[topo_name](makeNumeric(topo_param))


def getRouting(routing, topo):
    return ROUTING[routing](topo)
