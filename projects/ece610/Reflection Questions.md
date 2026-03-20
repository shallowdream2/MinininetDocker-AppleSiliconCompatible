# Reflection Questions
author: Chang Peng
## 1. How would you make this implementation scale with the number of clients?

要解决扩展性问题，需要消除系统中的单点瓶颈（Single Point of Failure/Bottleneck）以及同步阻塞。可以从以下三个维度进行改造：

负载均衡器自身的横向扩展 (Scale-out LB via DNS)：
目前的架构中只有一台 LB，当并发量极大时，LB 的网络带宽和 CPU 会率先被打满。引入 DNS 负载均衡 (Round-Robin DNS)，可以向客户端暴露多个负载均衡器的公网 IP。这样不仅能将海量入口流量分摊到不同的 LB 节点，还能实现跨可用区（Availability Zones）的扩展。

网络 I/O 模型的升级 (Asynchronous I/O)：
当前代码使用的是 threading 模型，在应对诸如 C10K（单机万级并发）问题时，频繁的线程上下文切换开销极大。在单节点层面，可以将基于线程的阻塞型 Socket 重写为基于事件驱动（Event-driven）的非阻塞 I/O 模型（如 Linux 的 epoll 或 Python 的 asyncio），或者采用天然支持高并发轻量级协程的语言（如 Go 语言的 Goroutines）来彻底解耦连接管理，大幅提升吞吐量。

后端服务的动态服务发现 (Dynamic Service Discovery)：
静态硬编码的 BACKENDS 列表无法应对突发流量。可以引入服务注册中心（如 Consul 或 Etcd），后端工作节点可以根据实时的计算资源水位自动进行扩缩容（Auto-scaling）。LB 动态拉取最新的可用节点列表进行流量分发，实现真正的弹性扩展。

## 2. In which cases are the round-robin a good load-balancing algorithm?

轮询（Round-Robin）的最大特点是静态且无状态，它不关心服务器当前的真实负载，也不关心请求的具体内容。因此，它只有在以下三个条件同时满足（即“高度同构”场景）时，才是一个优秀的算法：

同构的硬件资源 (Homogeneous Hardware)：
池子里的所有后端服务器（b1, b2, b3）在 CPU 算力、内存大小和网络带宽上必须完全一致。如果混合了高性能和老旧型号的机器，RR 依然会平均分配请求，导致老机器不堪重负而崩溃。

同质化的计算任务 (Homogeneous Workloads)：
这是最关键的一点。以本次的“图顶点计数”为例，只有当每个客户端发送的图文件（Graph Data）大小相近时，RR 才是极佳的选择。如果某个客户端发来一个包含千万个节点的超大图，而其他请求只是几十个节点的小图，RR 会导致处理大图的节点耗尽算力（引发队头阻塞 Head-of-Line Blocking），而其他节点却处于闲置状态。此时，应当改用最少连接数 (Least Connections) 等动态算法。

无状态服务 (Stateless Services)：
RR 无法保证特定的客户端始终路由到同一台服务器。对于像顶点计数这样不需要保存用户会话（Session）或历史状态的无状态计算任务，RR 是极其高效的，因为它省去了复杂的哈希计算和状态寻址开销。

## 3. How could you make this load balancer fault tolerant?

当前的系统极其脆弱，任何一个节点的宕机都会导致客户端请求失败。可以通过以下机制构建高容错系统：

主动健康检查机制 (Active Health Probing)：
LB 不应盲目地向后端发送请求。LB 需要在后台运行一个独立的看门狗线程，定期向所有的 bX 节点发送轻量级的探针（如 TCP Ping 或 HTTP Heartbeat）。如果某个节点连续 N 次未响应，LB 会通过加锁操作立刻将其从全局的轮询列表中剔除；当其恢复健康后，再重新动态加入。

客户端自动重试与请求幂等性 (Idempotency & Retries)：
由于图顶点计数是一个“只读”且幂等（Idempotent）的操作，多次计算不会改变数据的原始状态。因此，可以在 LB 或客户端内部实现重试机制。当 LB 发现分配的后端连接失败或超时，应捕获异常并静默地将该请求重新分配给下一个健康的后端，对客户端屏蔽底层的故障。

消除 LB 本身的单点故障 (High Availability via Consensus)：
如果 LB 节点宕机，整个集群就会瘫痪。需要部署主备多节点（Active-Passive 架构）的 LB 集群。可以引入类似 Raft 这样的分布式共识协议，确保主备节点之间的状态（如存活的后端列表）强一致性。一旦主控 LB 失去响应，集群能够迅速通过心跳超时触发选举，让备用节点无缝接管虚拟 IP（VIP），保证系统的持续可用性。