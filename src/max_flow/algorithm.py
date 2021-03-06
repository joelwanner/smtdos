from collections import namedtuple

from max_flow.flow import *
from max_flow.graph import *
from network.topology import Host, Link
from network.flow import Flow
from network.route import Route


class MaxFlow(object):
    def __init__(self, network):
        self.topology = network.topology
        self.victims = network.victims
        self.attackers = network.attackers
        self.flow = GraphFlow()

        self.graph = self.__create_graph()

    def __create_graph(self):
        vertices = []
        edges = []

        Cluster = namedtuple('Cluster', 'v v_in v_out')
        self.clusters = {}
        self.targeted_links = {}
        amp_factors = {}

        for h in self.topology.hosts:
            label = h.name
            v = Vertex(label)
            v_in = Vertex(label + "_in")
            v_out = Vertex(label + "_out")
            cluster = Cluster(v, v_in, v_out)

            vertices.extend(cluster)
            self.clusters[h] = cluster
            amp_factors[v] = h.amp_factor

            if h not in self.victims:
                e_in = Edge(v_in, v, h.receiving_cap)
                e_in_rev = Edge(v, v_in, 0)
                edges.extend([e_in, e_in_rev])

                e_out = Edge(v, v_out, h.sending_cap)
                e_out_rev = Edge(v_out, v, 0)
                edges.extend([e_out, e_out_rev])

        for l in self.topology.links:
            c1 = self.clusters[l.h1]
            c2 = self.clusters[l.h2]

            if l not in self.victims:
                e1 = Edge(c1.v_out, c2.v_in, l.capacity)
                e2 = Edge(c2.v_out, c1.v_in, l.capacity)
                e1_rev = Edge(c2.v_in, c1.v_out, 0)
                e2_rev = Edge(c1.v_in, c2.v_out, 0)

                # Victims are passive in the network: they are not allowed to send
                if l.h1 not in self.victims:
                    edges.extend([e1, e1_rev])
                if l.h2 not in self.victims:
                    edges.extend([e2, e2_rev])
            else:
                vl = Vertex("l%d" % (len(self.targeted_links) + 1))
                vertices.append(vl)
                self.targeted_links[l] = vl

                e1a = Edge(c1.v_out, vl, None)
                e1b = Edge(vl, c2.v_in, None)
                e2a = Edge(c2.v_out, vl, None)
                e2b = Edge(vl, c1.v_in, None)

                e1a_rev = Edge(vl, c1.v_out, 0)
                e1b_rev = Edge(c2.v_in, vl, 0)
                e2a_rev = Edge(vl, c2.v_out, 0)
                e2b_rev = Edge(c1.v_in, vl, 0)

                edges.extend([e1a, e1b, e2a, e2b, e1a_rev, e1b_rev, e2a_rev, e2b_rev])

        s = Vertex("s")
        vertices.append(s)
        for a in self.attackers:
            v = self.clusters[a].v
            e = Edge(s, v, None)
            edges.append(e)

        t = Vertex("t")
        vertices.append(t)
        self.sink = t

        for v in self.victims:
            if isinstance(v, Host):
                v_in = self.clusters[v].v_in
                e = Edge(v_in, t, None)
                e_rev = Edge(t, v_in, None)
                edges.extend([e, e_rev])

            elif isinstance(v, Link):
                vl = self.targeted_links[v]
                e = Edge(vl, t, None)
                e_rev = Edge(t, vl, None)
                edges.extend([e, e_rev])

        return FlowGraph(vertices, edges, s, t, amp_factors)

    def compute_flow(self):
        g = self.graph

        while True:
            paths = g.paths(g.source, g.sink, self.flow)

            if not paths:
                break

            best_path = None
            flow_to_send = 0
            max_benefit = 0

            for p in paths:
                residual, benefit = p.potential(self.flow)

                if benefit > max_benefit:
                    max_benefit = benefit
                    best_path = p
                    flow_to_send = residual

            if max_benefit <= 0:
                break

            self.send_flow(best_path, flow_to_send)
            paths.remove(best_path)

        return self.flow

    def send_flow(self, path, value):
        for e in path.edges:
            f = self.flow.get(e)
            delta = value * path.a[e]
            self.flow.set(e, f + delta)

            # Send negative flow in reverse direction, as in Ford-Fulkerson algorithm
            e_reverse = self.graph.get_edge(e.dest, e.src)
            if e_reverse:
                self.flow.set(e_reverse, f - delta)

    def flow_to_victim(self, v):
        if isinstance(v, Host):
            e = self.graph.get_edge(self.clusters[v].v_in, self.sink)
        elif isinstance(v, Link):
            e = self.graph.get_edge(self.targeted_links[v], self.sink)
        else:
            return 0

        return self.flow.get(e)

    def get_victims(self):
        victims = []
        for v in self.victims:
            if isinstance(v, Host) and self.flow_to_victim(v) > v.receiving_cap:
                victims.append(v)
            elif isinstance(v, Link) and self.flow_to_victim(v) > v.capacity:
                victims.append(v)

        return victims

    def get_flows(self):
        flows = []

        for l in self.topology.links:
            u_in = self.clusters[l.h1].v_in
            u_out = self.clusters[l.h1].v_out
            v_in = self.clusters[l.h2].v_in
            v_out = self.clusters[l.h2].v_out

            e1 = self.graph.get_edge(u_out, v_in)
            e2 = self.graph.get_edge(v_out, u_in)
            f1 = self.flow.get(e1)
            f2 = self.flow.get(e2)

            if f1 > 0:
                r = Route(l.h1, l.h2, hops=[l.h2])
                flows.append(Flow(r, f1))
            if f2 > 0:
                r = Route(l.h2, l.h1, hops=[l.h1])
                flows.append(Flow(r, f2))

        return flows
