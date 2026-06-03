# 横向规范：数据唯一性与 Canonical Result

## 目标

用户最终只看最有效、最可信的一组数据。失败、错误配置、无价值运行可以临时保存用于 debug，但不能混入最终 review。

## 数据状态机

```text
attempt -> valid_success -> raw
attempt -> failed_or_invalid -> scratch_failed minimal record
raw -> candidate -> canonical
old canonical -> archive or manifest reference only
```

## 数据分层

```text
runs/attempts/: 运行中的临时材料
runs/raw/: 通过有效性检查的成功运行原始材料
runs/scratch_failed/: 启动失败、配置错误、明显无效、性能异常但未定位的运行，默认只保留失败摘要和关键日志片段
results/canonical/: 唯一有效结果
reports/: 只引用 canonical 或明确标注的 debug 摘要
```

## 什么是无效数据

以下结果不能进入 canonical：

```text
serve 启动失败
single-request 失败
输出乱码或 tokenizer 错误
明显 OOM / worker crash
workload 参数跑错
prefix cache 本应命中但未命中且未解释
未按固定 workload 运行
日志缺失，无法追溯
性能极低且原因是配置错误
没有 run_id / command / manifest
```

## Canonical 更新规则

1. 新结果先写入 candidate。
2. 运行 canonical check。
3. 通过后替换 `results/canonical/`。
4. 旧 canonical 移入 archive 或只保留 manifest 引用。
5. report 只引用新的 canonical。

## 用户 review 规则

用户主报告不展示大量失败实验。只允许在 known bad configs 中简短写：

```text
Config X dropped: failed smoke test due to HCCL init error.
Config Y dropped: prefix cache did not hit because rendered prompt changed across sessions.
```

## 唯一性检查清单

```text
是否只有一个 final_launch_command.sh？
是否只有一份 final_metrics.json？
reports 是否引用 canonical path？
失败数据是否没有进入主表？
每个 canonical result 是否有 run_id 和 manifest？
```
