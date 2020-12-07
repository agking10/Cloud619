'''algorithm code is taken from http://www.gilles-bertrand.com/2014/03/disjkstra-algorithm-description-shortest-path-pseudo-code-data-structure-example-image.html'''
import numpy as np
from Hashed import HashHelperFunction

def DPIDPath(topo, path):
    dpidPath = []
    for switch in path:
        dpidPath.append(topo.id_gen(name = switch).dpid)
    
    return dpidPath


def WeightedHelperFunction(topo,src,dst):
    ''' hash's helper function:

    makes link dictionary without the certain core switches
    calls dijkstras on it

    make a new graph that blocks all 

    '''
    #print 'src: ' + src
    #print 'dst: ' + dst
    topoG = topo.g
    k = topo.k

    # create list of core switches
    core_switch_list = []
    for node in topoG.nodes():
        if(node[0]=='4'):
        	core_switch_list.append(node)
    
    # finds bucket for given src,dst pair
    flowHash = hash(src+dst)
    bucket_num = flowHash%4

    src_split = src.split("_")
    dst_split = dst.split("_")

    path = [src]

    if (src == dst):
        return path

    agg_switch = []
    agg_weights = []
    agg_layer = topo.layer_nodes(1)
    for switch in topo.graphDic[src].keys():
        if switch in agg_layer:
            for i in range(topo.graphDic[src][switch]):
                agg_switch.append(switch)
            agg_weights.append(topo.graphDic[src][switch])
    ind = hash(src + dst) % len(agg_switch)
    agg_up = agg_switch[ind]


    #agg_weights = np.array(agg_weights, dtype = float)
    #agg_weights /= agg_weights.sum()
    #agg_choices = np.arange(len(agg_switch))
    #agg_ind = np.random.choice(agg_choices, 1, p=agg_weights)[0]
    #agg_up = agg_switch[agg_ind]

    if (src_split[0] == dst_split[0]):
        remaining = BFS(topo.graphDic, agg_up, dst)
        path = path + list(remaining)
        return path #DPIDPath(topo, path)

    path.append(agg_up)

    core_switch = []
    core_weights = []
    core_layer = topo.layer_nodes(0)
    for switch in topo.graphDic[agg_up].keys():
        if switch in core_layer:
            for i in range(topo.graphDic[agg_up][switch]):
                core_switch.append(switch)
            core_weights.append(topo.graphDic[agg_up][switch])
    ind = hash(agg_up + dst) % len(core_switch)
    core_up = core_switch[ind]



    #core_weights = np.array(core_weights, dtype = float)
    #core_weights /= core_weights.sum()
    #core_choices = np.arange(len(core_switch))
    #core_ind = np.random.choice(core_choices, 1, p=core_weights)[0]
    #core_up = core_switch[core_ind]

    remaining = BFS(topo.graphDic, core_up, dst)
    path = path + list(remaining)
    return path #DPIDPaht(topo, path)

    
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




