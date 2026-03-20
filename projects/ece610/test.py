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

import time
import json
import re
import glob
import os

def run_auto_grader(net):
    print("\n" + "="*50)
    print("🤖 开始全自动判分测试 (Auto-Grader)")
    print("="*50)

    h1, h2, h3 = net.get('h1'), net.get('h2'), net.get('h3')
    lb, b1, b2, b3 = net.get('lb'), net.get('b1'), net.get('b2'), net.get('b3')

    # Discover all sample input files sorted by name
    sample_input_files = sorted(glob.glob('sample_inputs/sample_input_*.txt'))
    n = len(sample_input_files)
    print(f"\n[+] 发现 {n} 个输入文件: {[os.path.basename(f) for f in sample_input_files]}")

    print("\n[+] 1. 在后台启动所有服务器...")
    b1.cmd('python3 backend_server.py &')
    b2.cmd('python3 backend_server.py &')
    b3.cmd('python3 backend_server.py &')
    lb.cmd('python3 load_balancer.py &')
    time.sleep(2)  

    print(f"\n[+] 2. 执行单客户端顺序请求测试 (30 分测试项, 共 {n} 个输入)...")
    backends_hit = []
    for i, input_file in enumerate(sample_input_files):
        output = h1.cmd(f'python3 client.py {input_file} 10.0.0.9 5000')
        print(f"   [请求 {i+1}] 输入文件: {os.path.basename(input_file)}, 原始输出: {output.strip()}")

        match = re.search(r'(\{.*?\})', output)
        if match:
            try:
                resp = json.loads(match.group(1))
                backends_hit.append(resp.get('backend'))
            except json.JSONDecodeError:
                backends_hit.append(None)
        else:
            backends_hit.append(None)

    # Verify round-robin: first 3 responses must hit all 3 different backends,
    # and every subsequent response must follow the same cycling order.
    if len(backends_hit) >= 3 and None not in backends_hit:
        base_order = backends_hit[:3]
        if len(set(base_order)) == 3:
            rr_ok = all(backends_hit[i] == base_order[i % 3] for i in range(len(backends_hit)))
            if rr_ok:
                print(f"单点测试通过！完美的轮询顺序: {backends_hit}")
            else:
                print(f"单点测试失败！顺序错误: {backends_hit}")
        else:
            print(f"单点测试失败！前3个请求未分发到3个不同后端: {backends_hit[:3]}")
    else:
        print(f"单点测试失败！响应不足或存在错误: {backends_hit}")

    print("\n[+] 3. 执行多客户端并发请求测试 (30 分测试项)...")
    # Assign a different input file to each client (cycling through available files)
    input_h1 = sample_input_files[0 % n]
    input_h2 = sample_input_files[1 % n]
    input_h3 = sample_input_files[2 % n]

    p1 = h1.popen(f'python3 client.py {input_h1} 10.0.0.9 5000')
    p2 = h2.popen(f'python3 client.py {input_h2} 10.0.0.9 5000')
    p3 = h3.popen(f'python3 client.py {input_h3} 10.0.0.9 5000')

    out1, _ = p1.communicate()
    out2, _ = p2.communicate()
    out3, _ = p3.communicate()
    
    print(f"   [h1 ({os.path.basename(input_h1)}) 收到的响应] : {out1.decode().strip()}")
    print(f"   [h2 ({os.path.basename(input_h2)}) 收到的响应] : {out2.decode().strip()}")
    print(f"   [h3 ({os.path.basename(input_h3)}) 收到的响应] : {out3.decode().strip()}")
    print("   请人工确认上方三行：如果未报错、无卡顿，且成功返回了各自对应的 JSON 结果，说明并发测试通过！")

    print("\n[+] 4. 清理后台服务器进程...")
    b1.cmd('pkill -f backend_server.py')
    b2.cmd('pkill -f backend_server.py')
    b3.cmd('pkill -f backend_server.py')
    lb.cmd('pkill -f load_balancer.py')
    print("="*50 + "\n")




if __name__ == '__main__':
    topology = LoadBalancerTopo()
    network = Mininet(topo=topology, link=TCLink, controller=lambda name:RemoteController(name, ip='127.0.0.1', port=6633))
    network.start()


    lb_node = network.get('lb')
    lb_node.setIP('10.0.0.9/24', intf='lb-eth0')
    lb_node.setIP('20.0.0.2/24', intf='lb-eth1')
    

    lb_node.cmd('sysctl -w net.ipv4.ip_forward=0')


    run_auto_grader(network)

    CLI(network)

    network.stop()