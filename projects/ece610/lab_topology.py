from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Node, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import RemoteController
from mininet.log import setLogLevel, info

from mininet.node import Node

class LoadBalancerTopo(Topo):
    def build(self, delay = '0ms'):
        # -------------------------------------------------
        # TODO STUDENTS:
        # Create hosts h1, h2, h3 (Done)
        # Create backend hosts b1, b2, b3 (Done)
        # Create switches s1 and s2 (Done)
        # Create load balancer node (Done)
        # Assign IP addresses exactly as specified
        # -------------------------------------------------

        # IMPORTANT:
        # DO NOT rename hosts
        # DO NOT change interface names
        # Grader depends on exact naming
        # -------------------------------------------------
        
        # Network 1 (Left-hand Network)
        # hX = Clients
        h1 = self.addHost('h1', ip='10.0.0.2/24', defaultRoute='via 10.0.0.9')
        h2 = self.addHost('h2', ip='10.0.0.3/24', defaultRoute='via 10.0.0.9')
        h3 = self.addHost('h3', ip='10.0.0.4/24', defaultRoute='via 10.0.0.9')

        # Network 2 (Right-hand Network)
        # bX = Back-End Servers
        b1 = self.addHost('b1', ip='20.0.0.3/24', defaultRoute='via 20.0.0.2')
        b2 = self.addHost('b2', ip='20.0.0.4/24', defaultRoute='via 20.0.0.2')
        b3 = self.addHost('b3', ip='20.0.0.5/24', defaultRoute='via 20.0.0.2')

        # Load Balancer
        lb = self.addHost('lb') # configure IP addresses in the controller
        

        # Switches
        s1 = self.addSwitch(name="s1")
        s2 = self.addSwitch(name="s2")

        # Links
        # Left-hand Network
        self.addLink(h1, s1, cls=TCLink, delay=delay)
        self.addLink(h2, s1, cls=TCLink, delay=delay)
        self.addLink(h3, s1, cls=TCLink, delay=delay)

        # s1 to Load Balancer
        self.addLink(s1, lb, cls=TCLink, delay=delay)

        # ⬆s2 to Load Balancer
        self.addLink(s2, lb, cls=TCLink, delay=delay)

        # Right-hand Network
        self.addLink(b1, s2, cls=TCLink, delay=delay)
        self.addLink(b2, s2, cls=TCLink, delay=delay)
        self.addLink(b3, s2, cls=TCLink, delay=delay)

if __name__ == '__main__':
    topology = LoadBalancerTopo()
    network = Mininet(topo=topology, link=TCLink, controller=lambda name:RemoteController(name, ip='127.0.0.1', port=6633))
    network.start()

    lb_node = network.get('lb')
    lb_node.setIP('10.0.0.9/24', intf='lb-eth0')
    lb_node.setIP('20.0.0.2/24', intf='lb-eth1')
    lb_node.cmd('sysctl -w net.ipv4.ip_forward=0')

    CLI(network)

    network.stop()
