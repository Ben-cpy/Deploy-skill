# Term Glossary Template

- TTFT（Time To First Token）：从请求发出到首个 token 返回的时间，主要反映 prefill 和调度开销。
- ITL（Inter-token Latency）：相邻输出 token 之间的延迟，主要反映 decode 阶段速度。
- TPOT（Time Per Output Token）：平均每个输出 token 的生成时间，常用于衡量 decode 阶段吞吐。
- KV cache：Transformer decode 时保存历史 key/value 的缓存，长上下文和多轮会显著消耗显存。
- Prefix cache：复用相同 prompt 前缀对应 KV cache 的机制，用于降低重复 prefill。
- Offload：把 KV cache 从 HBM 转移到 CPU/远端等存储层，以容量换取传输开销。
- Preemption：KV cache 不足时系统暂停或重算请求，通常导致 tail latency 变差。
- HBM（High Bandwidth Memory）：GPU/NPU 上的高带宽显存，是长上下文 KV cache 的主要容量瓶颈。
