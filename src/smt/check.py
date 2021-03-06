from network.network import Network
from network.topology import *
from smt.encode import ModelEncoder
from smt.decode import ModelDecoder
from smt.solve import *


class AttackChecker:
    def __init__(self, topology, n_flows, victims=None, links=None, attackers=None, exhaustive=False):
        self.topology = topology
        self.n_flows = n_flows
        self.victims = victims
        self.target_links = links
        self.attackers = attackers
        self.exhaustive = exhaustive

        self.attacks = []
        self.verbose = False

    def check_network(self, network):
        encoder = ModelEncoder(network, self.n_flows)
        assertions = encoder.get_assertions()

        solver = SmtSolver(verbose=self.verbose)
        result = solver.solve(assertions)

        if result == sat:
            decoder = ModelDecoder(encoder.model, solver.model)
            network.flows = decoder.flows()
            network.victims = decoder.victims()
            network.attackers = decoder.attackers()

            return network
        else:
            return None

    def check_host_attacks(self):
        if not self.attackers:
            potential_attackers = [h for h in self.topology.hosts
                                   if not (isinstance(h, Server) or (self.victims and h in self.victims))]
        else:
            potential_attackers = self.attackers

        # Single victim is specified
        if self.victims and len(self.victims) == 1:
            # Check attack on single victim
            n = Network(self.topology, self.n_flows, self.victims, potential_attackers)
            attack = self.check_network(n)
            if attack:
                self.attacks.append(attack)
                return [attack]
            else:
                return []

        # Multiple or no victims are specified
        else:
            if self.victims:
                potential_victims = set(self.victims)
            else:
                if self.attackers:
                    potential_victims = set([h for h in self.topology.hosts if h not in self.attackers])
                else:
                    potential_victims = set(self.topology.hosts)

            while potential_victims:
                # Perform first check to see which hosts can be attacked
                print("Looking for attacks on %s" % potential_victims)
                e = Network(self.topology, self.n_flows, potential_victims, potential_attackers)
                attack = self.check_network(e)

                if attack:
                    if not self.exhaustive:
                        return [attack]

                    print("Potential victims: %s" % attack.victims)
                    host_victims = [v for v in attack.victims if isinstance(v, Host)]
                    amplifying_victims = [h for h in host_victims if isinstance(h, Server)]

                    if len(host_victims) == 1 or not amplifying_victims:
                        self.attacks.append(attack)
                        potential_victims -= set(attack.victims)
                    else:
                        # For more than one victim, there may be an attack possible -- check them individually
                        for v in host_victims:
                            potential_victims.remove(v)
                            print("Checking attack on victim %s" % v.__repr__())

                            attackers = [h for h in potential_attackers if h != v]
                            attack = self.check_network(Network(self.topology, self.n_flows, [v], attackers))

                            if attack:
                                self.attacks.append(attack)
                else:
                    break

            return self.attacks

    def check_link_attack(self):
        if not self.attackers:
            potential_attackers = [h for h in self.topology.hosts if not (isinstance(h, Server) or h == self.victims)]
        else:
            potential_attackers = self.attackers

        attack = self.check_network(Network(self.topology, self.n_flows, self.target_links, potential_attackers))

        if attack:
            return [attack]
        else:
            return []

    @classmethod
    def from_string(cls, s, n_flows):
        return parser.parse_attack(cls, s, n_flows)

    @classmethod
    def from_network(cls, n, n_flows):
        victim_hosts = [h for h in n.victims if isinstance(h, Host)]
        victim_links = [h for h in n.victims if isinstance(h, Link)]
        return cls(n.topology, n_flows, victim_hosts, victim_links, n.attackers)
