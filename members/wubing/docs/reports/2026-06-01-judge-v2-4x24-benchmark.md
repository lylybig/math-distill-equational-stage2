# judge_v2 4x24 集群基准简报

## 结论

截至 2026-06-01，`judge_v2` 总控已经可以调度四台 worker：

```text
10.220.69.172:8889  workers_total=24
10.220.69.153:8889  workers_total=24
10.220.69.85:8889   workers_total=24
10.220.69.89:8889   workers_total=24
```

统一入口：

```text
http://10.220.69.172:8890
```

在最初 96 条 accepted Lean certificate 的端到端单轮基准中，新四机集群相对旧 `10.220.69.172:8888` 单机服务约快 `2.11x`：

| 服务 | 并发配置 | 样本数 | accepted | 墙钟耗时 | 吞吐 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 新 `judge_v2` controller `:8890` | 4 台 x 24 workers = 96 | 96 | 96 | 22.73s | 253 条/分钟 |
| 旧 `simple-api` `:8888` | 1 台 x 24 workers | 96 | 96 | 47.98s | 120 条/分钟 |

补测异步接口后，`POST /jobs` + `/jobs/{id}/wait` 的 96 条端到端耗时为 `17.47s`，相对旧单机约快 `2.75x`。这更接近后续大批量生产调用方式。

随后做了更严格的三轮轮换测试：每轮每种模式各 96 条，先 warm-up，再轮换执行顺序，三种模式共 `864` 条正式 Lean 校验，全部 accepted。三轮均值显示：

| 服务/模式 | 样本 | accepted | 平均墙钟 | 平均吞吐 | 相对旧服务 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 旧 `simple-api :8888 /runs` | 3 x 96 | 288/288 | 37.09s | 155 条/分钟 | 1.00x |
| 新同步 `judge_v2 :8890 /verify` | 3 x 96 | 288/288 | 18.16s | 317 条/分钟 | 2.04x |
| 新异步 `judge_v2 :8890 /jobs` | 3 x 96 | 288/288 | 17.39s | 331 条/分钟 | 2.13x |

同样保持并发上限 `4 x 24 = 96`，将每轮样本数从 96 扩到 192 后，三轮均值仍约为 `2.02x`：

| 服务/模式 | 样本 | accepted | 平均墙钟 | 平均吞吐 | 相对旧服务 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 旧 `simple-api :8888 /runs` | 3 x 192 | 576/576 | 69.52s | 166 条/分钟 | 1.00x |
| 新同步 `judge_v2 :8890 /verify` | 3 x 192 | 576/576 | 34.28s | 337 条/分钟 | 2.03x |
| 新异步 `judge_v2 :8890 /jobs` | 3 x 192 | 576/576 | 34.44s | 335 条/分钟 | 2.02x |

严格测试原始结果：

```text
artifacts/judge_v2_bench/strict-1780320258-f1d00bab.json
artifacts/judge_v2_bench/strict-1780320830-06e3782b.json
```

复现实验脚本：

```text
members/wubing/scripts/deploy/benchmark_judge_v2_vs_old.py
```

## 测试口径

旧服务 `10.220.69.172:8888` 是 `simple-api`，真实校验入口是 `/runs`，不是 direct `/verify`。新服务 `10.220.69.172:8890` 是 `judge_v2-control`，入口是 `/verify`，由总控调度到四台 worker。

本次比较采用“完成同一批 certificate 校验”的端到端耗时：

- 每条 problem 使用唯一 `problem.id`，代码中加入唯一 comment，避免命中已有缓存。
- certificate 类型为同一类 accepted Lean 证明。
- 旧服务使用 `/runs`，`max_workers=24`，`cache=false`。
- 新服务使用 `/verify`，客户端并发发出 96 条请求，总控可调度 96 个 worker 槽位。
- 使用客户端墙钟时间计算吞吐，避免使用旧服务 summary 中的 aggregate `elapsedSeconds`。

## 96 条基准结果

### 严格三轮测试

严格测试参数：

- suite id: `strict-1780320258-f1d00bab`
- warm-up: 每种模式先跑 8 条，不计入正式结果。
- 正式轮次: 3 轮。
- 每轮每种模式: 96 条 accepted Lean certificate。
- 顺序轮换:
  - 第 1 轮: old, sync, async
  - 第 2 轮: sync, async, old
  - 第 3 轮: async, old, sync
- 每条请求使用唯一 `problem.id` 和唯一代码 comment。
- 旧服务使用 `/runs`，`max_workers=24`，`cache=false`。
- 新同步使用 `/verify`，客户端并发 96。
- 新异步使用 `/jobs` 并发提交，再并发 `/jobs/{job_id}/wait`。

正式结果：

| 模式 | 第 1 轮 | 第 2 轮 | 第 3 轮 | 均值 | 中位数 | 平均吞吐 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| old `/runs` | 37.83s | 36.87s | 36.56s | 37.09s | 36.87s | 155 条/分钟 |
| sync `/verify` | 18.79s | 17.84s | 17.86s | 18.16s | 17.86s | 317 条/分钟 |
| async `/jobs` | 17.40s | 17.71s | 17.06s | 17.39s | 17.40s | 331 条/分钟 |

严格测试结论：

```text
sync /verify vs old /runs:   2.04x
async /jobs  vs old /runs:   2.13x
async /jobs  vs sync /verify: 1.04x
```

这组结果比前面的单轮测试更稳。它说明新 4x24 集群的主要收益来自四台 worker 的并发扩展；异步接口在严格轮换测试中略快于同步接口，但差距只有约 `4%`，因此更重要的价值是快速入队、便于上游管理长耗时任务，而不是单条任务显著变快。

### 严格三轮测试，192 条样本

该轮测试保持实际 worker 并发不变：

```text
4 台 x 24 workers = 96 并发槽位
```

仅将每轮样本数从 96 扩到 192，用于观察样本数超过并发槽位后，需要排第二批队列时的吞吐表现。

严格测试参数：

- suite id: `strict-1780320830-06e3782b`
- warm-up: 每种模式先跑 8 条，不计入正式结果。
- 正式轮次: 3 轮。
- 每轮每种模式: 192 条 accepted Lean certificate。
- 顺序轮换:
  - 第 1 轮: old, sync, async
  - 第 2 轮: sync, async, old
  - 第 3 轮: async, old, sync
- 客户端并发: 96。
- 旧服务使用 `/runs`，`max_workers=24`，`cache=false`。
- 新同步使用 `/verify`。
- 新异步使用 `/jobs` 并发提交，再并发 `/jobs/{job_id}/wait`。

正式结果：

| 模式 | 第 1 轮 | 第 2 轮 | 第 3 轮 | 均值 | 中位数 | 平均吞吐 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| old `/runs` | 69.98s | 69.82s | 68.77s | 69.52s | 69.82s | 166 条/分钟 |
| sync `/verify` | 35.63s | 34.97s | 32.23s | 34.28s | 34.97s | 337 条/分钟 |
| async `/jobs` | 36.60s | 34.63s | 32.10s | 34.44s | 34.63s | 335 条/分钟 |

严格 192 条结论：

```text
sync /verify vs old /runs:   2.03x
async /jobs  vs old /runs:   2.02x
async /jobs  vs sync /verify: 0.995x
```

这轮结果说明：当样本数从 96 扩到 192，但实际并发槽位仍为 96 时，新集群依然保持约 `2x` 的端到端吞吐优势。同步和异步在这种吞吐测试下几乎持平；异步接口的主要优势仍是快速入队和更适合长任务/大批量任务管理。

严格测试结束后，总控和四台 worker 均恢复空闲：

```text
controller queue_size=0
10.220.69.172 workers_busy=0 / workers_total=24
10.220.69.153 workers_busy=0 / workers_total=24
10.220.69.85  workers_busy=0 / workers_total=24
10.220.69.89  workers_busy=0 / workers_total=24
```

### 单轮同步 `/verify`

新 `judge_v2` 四机集群：

```json
{
  "name": "new_4x24_controller_8890_n96",
  "n": 96,
  "wall_seconds": 22.7345,
  "throughput_per_min": 253.36,
  "accepted": 96,
  "p50_client_ms": 12877,
  "p95_client_ms": 20825,
  "max_client_ms": 22697
}
```

调度分布：

```text
10.220.69.172:8889  26 条
10.220.69.153:8889  23 条
10.220.69.85:8889   22 条
10.220.69.89:8889   25 条
```

旧 `simple-api` 单机：

```json
{
  "name": "old_simple_api_8888_single_host_n96",
  "n": 96,
  "status": "done",
  "wall_seconds": 47.9845,
  "throughput_per_min": 120.04,
  "accepted": 96,
  "summary_metrics": "96A / 0R / 0E"
}
```

对比：

```text
wall_time_speedup = 47.9845 / 22.7345 = 2.11x
throughput_speedup = 253.36 / 120.04 = 2.11x
```

### 异步 `/jobs`

异步接口补测使用同样规模的 96 条 accepted Lean certificate：

- `POST /jobs` 并发提交 96 个 job。
- 再并发调用 `/jobs/{job_id}/wait?timeout_seconds=220` 等待结果。
- 每条 problem 使用唯一 `problem.id`，代码中加入唯一 comment，避免命中已有缓存。

结果：

```json
{
  "name": "async_jobs_4x24_controller_8890_n96",
  "n": 96,
  "submit_wall_seconds": 0.2936,
  "wait_wall_seconds": 17.1716,
  "total_wall_seconds": 17.4651,
  "throughput_per_min": 329.80,
  "accepted": 96,
  "done": 96,
  "submit_p50_ms": 140,
  "submit_p95_ms": 193,
  "wait_p50_ms": 10167,
  "wait_p95_ms": 15397,
  "result_elapsed_p50_ms": 4078,
  "result_elapsed_p95_ms": 7362
}
```

异步调度分布：

```text
10.220.69.172:8889  27 条
10.220.69.153:8889  22 条
10.220.69.85:8889   22 条
10.220.69.89:8889   25 条
```

对比：

```text
异步 /jobs vs 旧 8888:
wall_time_speedup = 47.9845 / 17.4651 = 2.75x
throughput_speedup = 329.80 / 120.04 = 2.75x

异步 /jobs vs 同步 /verify:
wall_time_speedup = 22.7345 / 17.4651 = 1.30x
throughput_speedup = 329.80 / 253.36 = 1.30x
```

注意：异步补测发生在同步基准之后，worker 进程和 Lean 相关缓存可能已经预热，因此 `1.30x` 不应解释为接口本身必然带来的纯性能增益。更稳妥的结论是：异步接口已经验证可用，并且更适合作为大批量校验的生产调用方式；它可以快速入队，避免调用方长时间阻塞在单个同步 HTTP 请求上。

## 48 条小样本结果

48 条样本不足以体现 4 台机器的并发上限，因为旧单机 `:8888` 的 24 worker 已经能较快完成这批任务。

| 服务 | 样本数 | accepted | 墙钟耗时 | 吞吐 |
| --- | ---: | ---: | ---: | ---: |
| 新 `judge_v2` controller `:8890` | 48 | 48 | 18.98s | 152 条/分钟 |
| 旧 `simple-api` `:8888` | 48 | 48 | 19.50s | 148 条/分钟 |

该结果说明：当任务规模接近或小于单机并发容量时，分布式总控的优势不明显；当并发规模超过旧单机 24 槽位后，4x24 集群优势明显。

## 当前健康状态

基准结束后，四台 worker 和总控均恢复空闲：

```text
controller queue_size=0
10.220.69.172 workers_busy=0 / workers_total=24
10.220.69.153 workers_busy=0 / workers_total=24
10.220.69.85  workers_busy=0 / workers_total=24
10.220.69.89  workers_busy=0 / workers_total=24
```

## 使用建议

- 本机或上游程序统一请求 `http://10.220.69.172:8890`。
- 对大量 Lean certificate 校验，优先使用异步 `/jobs` 接口，避免单个 HTTP 同步请求等待过长。
- 24 workers 是当前四台机器的高并发配置；如果线上已有服务出现 CPU/内存压力，可以先把单机 worker 数降到 16，再复测吞吐和稳定性。
- 后续如果加入 `10.220.69.90`，总并发可从 96 扩到 120；加入前应先跑 `GET /health` 和真实 accepted smoke。
