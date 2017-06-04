from network.execution import Execution
from network.network import *
from smt.encode import ModelEncoder
from smt.decode import ModelDecoder
from smt.solver import *


class AttackChecker:
    def __init__(self, network, victim, attackers):
        self.network = network
        self.victim = victim
        self.attackers = attackers

        self.attack = None
        self.verbose = False

    def __check_execution(self, execution):
        encoder = ModelEncoder(execution, 6)
        assertions = encoder.get_assertions()

        solver = SmtSolver(verbose=self.verbose)
        result = solver.solve(assertions)

        if result == sat:
            self.attack = execution
            smt_model = solver.model

            decoder = ModelDecoder(encoder.model, smt_model)
            self.attack.flows = decoder.flows()
            return True
        else:
            return False

    def check(self):
        if not self.attackers or not self.victim:
            regular_hosts = []
            for h in self.network.hosts:
                if not (isinstance(h, Server) or h == self.victim):
                    regular_hosts.append(h)
        else:
            regular_hosts = self.attackers

        if self.victim:
            self.attackers = regular_hosts
            e = Execution(self.network, self.victim, regular_hosts)
            return self.__check_execution(e)
        else:
            for v in self.network.hosts:
                a = [h for h in regular_hosts if h != v]
                e = Execution(self.network, v, a)

                if self.__check_execution(e):
                    self.victim = v
                    self.attackers = a
                    return True

            return False

    @classmethod
    def from_string(cls, s):
        return parser.parse_attack(s)
