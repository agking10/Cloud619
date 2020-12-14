'''
 based on riplpox 
'''

import logging

import sys

from struct import pack
from zlib import crc32

from pox.core import core
import pox.openflow.libopenflow_01 as of

from pox.lib.revent import EventMixin
from pox.lib.util import dpidToStr
from pox.lib.recoco import Timer
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.udp import udp
from pox.lib.packet.tcp import tcp
from pox.lib.addresses import EthAddr, IPAddr

from util import buildTopo, getRouting
from Hashed import HashHelperFunction
from Dijkstras import dijkstraHelperFunction


log = core.getLogger()

# Number of bytes to send for packet_ins
MISS_SEND_LEN = 2000

class Switch(EventMixin):
    def __init__(self):
        self.connection = None
        self.dpid = None
        self.ports = None

    def connect(self, connection):
        if self.dpid is None:
            self.dpid = connection.dpid
        assert self.dpid == connection.dpid
        self.connection = connection
    
    def send_packet_data(self, outport, data = None):
        msg = of.ofp_packet_out(in_port=of.OFPP_NONE, data = data)
        msg.actions.append(of.ofp_action_output(port = outport))
        self.connection.send(msg)
    
    def send_packet_bufid(self, outport, buffer_id = -1):
        msg = of.ofp_packet_out(in_port=of.OFPP_NONE)
        msg.actions.append(of.ofp_action_output(port = outport)) 
        msg.buffer_id = buffer_id
        self.connection.send(msg)
                        
    def install(self, port, match, modify = False, buf = -1, idle_timeout = 0, hard_timeout = 0):
        msg = of.ofp_flow_mod()
        #msg.priority = 42
        msg.match = match
        if modify:
            msg.command = of.OFPFC_MODIFY_STRICT
        else: 
            msg.command = of.OFPFC_ADD
        msg.idle_timeout = idle_timeout
        msg.hard_timeout = hard_timeout
        msg.actions.append(of.ofp_action_output(port = port))
        #msg.buffer_id = buf          
        msg.flags = of.OFPFF_SEND_FLOW_REM

        self.connection.send(msg)

    def stat(self, port):
        msg = of.ofp_stats_request()
        # msg.type = of.OFPST_FLOW
        msg.body = of.ofp_flow_stats_request()
        #msg.body.match.in_port = port
        self.connection.send(msg) 
 
class DCController(EventMixin):
    def __init__(self, t, r):
        self.switches = {}  # [dpid]->switch
        self.macTable = {}  # [mac]->(dpid, port) a distributed MAC table
        self.t = t          # Topo object
        self.r = r          # Routng object
        self.mode = 'proactive'
        self.all_switches_up = False
        core.openflow.addListeners(self)

    def getSrcIp(self, packet):
        l = str(packet.payload).split(">")[1].split(" ")[1].split(">")
        return str(l[0])

    def getDestIp(self, packet):
        l = str(packet.payload).split(">")[1].split(" ")[1].split(">")
        return str(l[1])

    def getMacSrcAddr(self, packet):
        l = str(packet.payload).split(">")[0].split(" ")
        return str(l[len(l)-1])

    def getMacDestAddr(self, packet):
        l = str(packet.payload).split(">")[1].split(" ")
        return str(l[0])
    def _raw_dpids(self, arr):
        "Convert a list of name strings (from Topo object) to numbers."
        return [self.t.id_gen(name = a).dpid for a in arr]
    
    def _ecmp_hash(self, packet):
        ''' Return an ECMP-style 5-tuple hash for TCP/IP packets, otherwise 0.
        RFC2992 '''
        pass
        
    def _flood(self, event):
        ''' Broadcast to every output port '''
        packet = event.parse()
        dpid = event.dpid
        in_port = event.port
        t = self.t
     
        nodes = t.layer_nodes(t.LAYER_EDGE)
        dpids = self._raw_dpids(t.layer_nodes(t.LAYER_EDGE))
        

        for sw in self._raw_dpids(t.layer_nodes(t.LAYER_EDGE)):
            ports = []
            sw_name = t.id_gen(dpid = sw).name_str()
            switch_Hosts = []
            for host in t.layer_nodes(t.LAYER_HOST):
                if((host[0] == sw_name[0])and (host[2] == sw_name[2])):
        	        switch_Hosts.append(host)
            for host in switch_Hosts:
                sw_port, host_port = t.port(sw_name, host)
                if sw != dpid or (sw == dpid and in_port != sw_port):
                    ports.append(sw_port)
            for port in ports:
                self.switches[sw].send_packet_data(port, event.data)

    

    def _install_reactive_path(self, event, out_dpid, final_out_port, packet):
        ''' Install entries on route between two switches. '''
        in_name = self.t.id_gen(dpid = event.dpid).name_str()
        out_name = self.t.id_gen(dpid = out_dpid).name_str()
        # hash_ = self._ecmp_hash(packet)
        route = self.r.get_route(in_name, out_name)
        match = of.ofp_match.from_packet(packet)
        for i, node in enumerate(route):
            node_dpid = self.t.id_gen(name = node).dpid
            if i < len(route) - 1:
                next_node = route[i + 1]
                out_port, next_in_port = self.t.port(node, next_node)
            else:
                out_port = final_out_port
            self.switches[node_dpid].install(out_port, match, idle_timeout = 10)
        
    def _handle_FlowStatsReceived (self, event):
        pass

    def _handle_PacketIn(self, event):
        if not self.all_switches_up:
            log.info("Saw PacketIn before all switches were up - ignoring.")
            return
        else:
            if self.mode == 'reactive':
                self._handle_packet_reactive(event)
            elif self.mode == 'proactive':
                self._handle_packet_proactive(event)



    def _handle_packet_reactive(self, event):
        packet = event.parsed
        dpid = event.dpid
        in_port = event.port       
        t = self.t


        #if packet is notipv4, ignore
        if(str(packet.src) == "2048"):
            return

        #get soruce and destination mac addresses
        srcMac = packet.src
        destMac = packet.dst

        #add source mac address in mac table, with dpid and in_port as values
        self.macTable[str(srcMac)] = (dpid, in_port)
        #print(self.macTable)
        #print("srcip: "+str(packet.next.srcip))
        #print("destip: " + str(packet.next.dstip))
           

        #if destination mac address is in mac table, install reactive path. else flood. 
        if str(destMac) in self.macTable:
            out_dpid, out_port = self.macTable[str(destMac)]
            self._install_reactive_path(event, out_dpid, out_port, packet)
            self.switches[out_dpid].send_packet_data(out_port, event.data)
        else:
            self._flood(event)
        
    def _handle_packet_proactive(self, event):
        packet = event.parse()
        #self._flood(event)
        if packet.dst.is_multicast:
            self._flood(event)
        else:
            hosts = self._raw_dpids(self.t.layer_nodes(self.t.LAYER_HOST))
            if self.t.id_gen(mac = packet.src.toStr()).dpid not in hosts:
                raise Exception("unrecognized src: %s" % packet.src)
            if self.t.id_gen(mac = packet.dst.toStr()).dpid not in hosts:
                raise Exception("unrecognized dst: %s" % packet.dst)
            raise Exception("known host MACs but entries weren't pushed down?!?")


    def _handle_ConnectionUp(self, event):
        sw = self.switches.get(event.dpid)
        sw_str = dpidToStr(event.dpid)
        sw_name = self.t.id_gen(dpid = event.dpid).name_str()
        self.macTable.clear() #clear macTable when there is a new conection
        
        if sw_name not in self.t.switches():
            log.warn("Ignoring unknown switch %s" % sw_str)
            return

        if sw is None:
            log.info("Added a new switch %s" % sw_name)
            sw = Switch()
            self.switches[event.dpid] = sw
            sw.connect(event.connection)
        else:
            log.debug("Odd - already saw switch %s come up" % sw_str)
            sw.connect(event.connection)

        sw.connection.send(of.ofp_set_config(miss_send_len=MISS_SEND_LEN))

        if len(self.switches)==len(self.t.switches()):
            log.info("All of the switches are up")
            if self.mode == 'proactive':
                self._install_proactive_flows()
                log.info("Routing is complete") 
            self.all_switches_up = True

    def _install_proactive_flows(self):
        t = self.t
        for src in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
            for dst in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
                if (src == dst):
                    continue
                self._install_proactive_path(src, dst)

    def _install_proactive_flows_alt(self):
        t = self.t
        for src in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_EDGE))):
            for dst in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
                self._install_proactive_path_single(src, dst)

        for src in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_AGG))):
            for dst in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
                self._install_proactive_path_single(src, dst)

        for src in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_CORE))):
            for dst in sorted(self._raw_dpids(t.layer_nodes(t.LAYER_HOST))):
                self._install_proactive_path_single(src, dst)


    def _install_proactive_path_single(self, src, dst):
        src_sw = self.t.id_gen(dpid = src)
        src_sw_name = src_sw.name_str()
        dst_sw = self.t.id_gen(dpid = dst)
        dst_sw_name = dst_sw.name_str()
        route = self.r.get_route(src_sw_name, dst_sw_name)
   
        match = of.ofp_match()
        match.dl_dst = EthAddr(dst_sw.mac_str()).toRaw()
#        match.dl_type = 0x800
#        match.set_nw_dst(IPAddr(dst_sw.ip_str()), 32)
#        match.tp_dst = 80

        node_dpid = self.t.id_gen(name = route[0]).dpid
        next_node = route[1]
        out_port, next_in_port = self.t.port(route[0], next_node)
        self.switches[node_dpid].install(next_in_port, match)
 

    def _install_proactive_path(self, src, dst):
        """Install entries on route between two hosts based on MAC addrs.
    
        src and dst are unsigned ints.
        """
        src_sw = self.t.id_gen(dpid = src)
        src_sw_name = src_sw.name_str()
        dst_sw = self.t.id_gen(dpid = dst)
        dst_sw_name = dst_sw.name_str()
        route = self.r.get_route(src_sw_name, dst_sw_name)

        # Form OF match
        match = of.ofp_match()

        #match.dl_type = 0x800
        match.dl_src = EthAddr(src_sw.mac_str()).toRaw()
        match.dl_dst = EthAddr(dst_sw.mac_str()).toRaw()
        #match.set_nw_src(IPAddr(src_sw.ip_str()), 32)
        #match.set_nw_dst(IPAddr(dst_sw.ip_str()), 32)

        for i in range(1, len(route) - 1):
            node_dpid = self.t.id_gen(name = route[i]).dpid
            next_node = route[i + 1]
            out_port, next_in_port = self.t.port(route[i], next_node)
            self.switches[node_dpid].install(out_port, match)

    def _src_dst_hash(self, src_dpid, dst_dpid):
        "Return a hash based on src and dst dpids."
        return crc32(pack('QQ', src_dpid, dst_dpid))


def launch(topo = None, routing = None):
    if not topo:
        raise Exception ("Please specify the topology")
    else: 
        t = buildTopo(topo)
    r = getRouting(routing, t)

    core.registerNew(DCController, t, r)
    log.info("*** Controller is running")

