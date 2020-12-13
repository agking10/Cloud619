'''algorithm code is taken from http://www.gilles-bertrand.com/2014/03/disjkstra-algorithm-description-shortest-path-pseudo-code-data-structure-example-image.html'''
import numpy as np
from Hashed import HashHelperFunction

def DPIDPath(topo, path):
    dpidPath = []
    for switch in path:
        dpidPath.append(topo.id_gen(name = switch).dpid)
    
    return dpidPath


def ECMPHelperFunction(topo,src,dst):
    ''' hash's helper function:

    makes link dictionary without the certain core switches
    calls dijkstras on it

    make a new graph that blocks all 

    '''
    #print 'src: ' + src
    #print 'dst: ' + dst

    # create list of core switches
    
    # finds bucket for given src,dst pair

    path = [src]

    if (src == dst):
        return path

    if (src in topo.layer_nodes(3)):
        return pathFromHost(src, dst, path, topo)
    elif (src in topo.layer_nodes(2)):
        return pathFromEdge(src, dst, path, topo)
    elif (src in topo.layer_nodes(1)):
        return pathFromAgg(src, dst, path, topo)
    elif (src in topo.layer_nodes(0)):
        return pathFromCore(src, dst, path, topo)
    return None

def pathFromHost(src, dst, path, topo):
    path.append(topo.graphDic[src].keys()[0])
    edge = path[1]
    return pathFromEdge(edge, dst, path, topo)

def pathFromEdge(src, dst, path, topo):
    if (dst in topo.graphDic[src].keys()):
        path.append(dst)
        return path
    agg_switch = []
    agg_weights = []
    agg_layer = topo.layer_nodes(1)
    for switch in topo.graphDic[src].keys():
        if switch in agg_layer:
            agg_switch.append(switch)
    ind = hash(src + dst) % len(agg_switch)
    agg = agg_switch[ind]
    path.append(agg)
    return pathFromAgg(agg, dst, path, topo)


def pathFromAgg(src, dst, path, topo):
    src_pod = src.split("_")[0]
    dst_pod = dst.split("_")[0]
    if (src_pod == dst_pod):
        remaining = BFS(topo.graphDic, src, dst)
        path = path + list(remaining)[1:]
        return path

    core_switch = []
    core_weights = []
    core_layer = topo.layer_nodes(0)
    for switch in topo.graphDic[src].keys():
        if switch in core_layer:
            core_switch.append(switch)
    ind = hash(src + dst) % len(core_switch)
    core = core_switch[ind]
    path.append(core)
    return pathFromCore(core, dst, path, topo)


def pathFromCore(src, dst, path, topo):
    remaining = BFS(topo.graphDic, src, dst)
    path = path + list(remaining)[1:]
    return path

    
class Node():
    def __init__(self, data, prev):
        self.data = data
        self.prev = prev

    def __eq__(self, other):
        return self.data == other.data

def BFS(graph, src, dst):
    visited = set()

    queue = list()

    queue.append(Node(src, None))
    end = None
    while len(queue) > 0:
        elem = queue.pop(0)
	if elem.data == dst:
            end = elem
            break

        for child in graph[elem.data].keys():
            if child not in visited:
                visited.add(child)
                queue.append(Node(child, elem))
     
    path = []
    while end is not None:
        path.insert(0, end.data)
        end = end.prev
    return path




