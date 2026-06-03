# Matplotlib Paper-Style Visualization Guideline

## 0. Scope

This guideline is for Python `matplotlib` figure generation.

It is not for image-generation models.

All text inside figures must be English.

Do not use Chinese characters in:

- title
- axis label
- legend
- tick label
- annotation
- figure text
- saved filename if possible

---

## 1. Global Style Rules

Use a clean academic paper style.

```python
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.6,
    "lines.markersize": 4.5,
    "grid.linewidth": 0.5,
})
````

Default figure style:

```python
fig, ax = plt.subplots(figsize=(3.4, 2.2))
ax.grid(axis="y", linestyle="-", linewidth=0.5, alpha=0.35)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

Export rule:

```python
plt.tight_layout()
plt.savefig("figure.pdf", bbox_inches="tight")
plt.savefig("figure.png", dpi=300, bbox_inches="tight")
```

---

## 2. Color Palette

Use a small, stable color set.

### Recommended Role-Based Palette

```python
COLORS = {
    "ours": "#C1121F",          # strong red
    "baseline_1": "#1F77B4",    # blue
    "baseline_2": "#59A14F",    # green
    "baseline_3": "#F2A900",    # amber
    "baseline_4": "#8A8A8A",    # gray
    "upper_bound": "#222222",   # black
    "oracle": "#6F4E7C",        # muted purple
    "grid": "#E6E6E6",
}
```

### Encoding Rules

* `Ours`: red solid line or red bar.
* Strong baseline: blue.
* Other baselines: green, amber, gray.
* Upper bound / ideal / oracle: black dashed line.
* Ablation variants: lighter colors or gray-scale variants.
* Do not use more than 5 colors in one figure.
* Do not rely only on color. Use markers, line styles, or hatches when needed.

---

## 3. Figure Type Selection

## 3.1 Comparison Figure

Use when the goal is to show which method is better.

Recommended chart:

* grouped bar
* line chart with categorical x-axis

Use when:

* comparing methods
* comparing systems
* comparing configurations
* showing relative improvement

Generation rules:

```python
# x-axis: workload / scenario / dataset / setting
# y-axis: one metric only
# bars or lines: methods
# highlight Ours
```

Style:

* Put baselines before `Ours`.
* Put `Ours` last or visually highlighted.
* Keep the same method order across all figures.
* Use one y-axis only.

Good axis labels:

```text
Workload
Scenario
Latency (ms)
Throughput (ops/s)
Normalized Performance
Accuracy (%)
Memory Usage (GB)
```

---

## 3.2 Scaling Figure

Use when the goal is to show behavior under increasing pressure.

Recommended chart:

* line chart

Use when x-axis is ordered or continuous:

* input size
* data size
* concurrency
* request rate
* number of devices
* model size
* cache size
* block size
* time
* version

Generation rules:

```python
# x-axis: stress factor
# y-axis: response metric
# each line: one method or configuration
```

Style:

* Use markers for each line.
* Use log-scale only when the x-axis spans orders of magnitude.
* Mark saturation or collapse points only if necessary.
* Do not mix unrelated metrics in the same plot.

Example:

```python
ax.plot(x, y_baseline, marker="o", color=COLORS["baseline_1"], label="Baseline")
ax.plot(x, y_ours, marker="s", color=COLORS["ours"], label="Ours")
ax.set_xlabel("Concurrency")
ax.set_ylabel("Latency (ms)")
```

---

## 3.3 Small Multiples Figure

Use when the same question is repeated across many scenarios.

Recommended chart:

* grid of subplots

Use when there are two scenario dimensions:

* dataset × method
* workload × metric
* compression algorithm × image
* model × input length
* hardware × workload

Generation rules:

```python
# each subplot uses the same visual grammar
# same x-axis meaning
# same method colors
# shared legend
```

Style:

* Prefer `2x2`, `2x3`, or `3x3`.
* Avoid more than `3x4` in the main paper figure.
* Use shared x/y axes when possible.
* Put subplot titles in short English labels.

Example titles:

```text
(a) Dataset A
(b) Dataset B
(c) Dataset C
(d) Dataset D
```

---

## 3.4 Ablation Figure

Use when the goal is to show where the gain comes from.

Recommended chart:

* bar chart
* stepwise line chart
* compact table if values are exact and few

Use when:

* adding components one by one
* removing components one by one
* comparing design variants
* validating system mechanisms

Generation rules:

```python
# x-axis: component setting
# y-axis: one core metric
# order follows design logic
```

Example x-axis:

```text
Base
+ Cache
+ Scheduler
+ Compression
+ Final
```

Style:

* Keep the order causal.
* Do not sort by score.
* Use gray for intermediate variants.
* Use red for final method.

---

## 3.5 Sensitivity Figure

Use when the goal is to show robustness to parameters.

Recommended chart:

* line chart
* small multiples if multiple parameters exist

Use when varying:

* threshold
* chunk size
* batch size
* sampling rate
* cache size
* timeout
* weight
* ratio

Generation rules:

```python
# x-axis: parameter value
# y-axis: core metric
# mark default setting
```

Style:

* Highlight default setting with a vertical dashed line.
* Do not show parameters with negligible impact unless needed.
* Use one parameter per subplot.

Example:

```python
ax.axvline(default_value, color=COLORS["upper_bound"], linestyle="--", linewidth=1.0)
ax.text(default_value, y_pos, "Default", rotation=90, va="bottom", ha="right")
```

---

## 3.6 Breakdown Figure

Use when the goal is to explain composition.

Recommended chart:

* stacked bar
* grouped bar
* pie chart is not recommended

Use when showing:

* time breakdown
* memory breakdown
* cost breakdown
* storage breakdown
* error type distribution
* workload composition

Generation rules:

```python
# x-axis: scenario
# stacked segments: components
# y-axis: total amount or percentage
```

Style:

* Use stacked bars only when components add up naturally.
* If components do not add up, use grouped bars.
* Use percentages only when total normalization is meaningful.

---

## 3.7 Evidence Table

Use when exact values matter more than visual trend.

Use tables for:

* testbed
* dataset
* workload
* configuration
* hyperparameters
* summary numbers
* cost
* artifact information

Do not use tables for:

* trends
* scaling behavior
* multi-point performance curves

Recommended columns:

```text
Name | Setting | Value | Unit
Workload | Input | Output | Metric
Method | Result | Improvement | Notes
```

---

## 4. Layout Rules

## 4.1 Single-Column Figure

Use for one simple message.

```python
figsize = (3.4, 2.2)
```

Best for:

* main comparison
* one scaling curve
* one ablation

## 4.2 Double-Column Figure

Use for dense evidence.

```python
figsize = (6.8, 2.4)
```

Best for:

* small multiples
* multiple related metrics
* broad scenario coverage

## 4.3 Slide Figure

Use larger fonts and fewer elements.

```python
figsize = (7.0, 4.0)
```

Rules:

* maximum 2–3 methods
* maximum 4 subplots
* title should state the conclusion
* legend should be minimal

---

## 5. Axis and Legend Rules

Axis labels must include units.

Good:

```text
Latency (ms)
Throughput (GB/s)
Memory Usage (GB)
Compression Ratio
Accuracy (%)
Normalized Speedup
```

Bad:

```text
Latency
Performance
Result
Value
```

Legend rules:

* Keep method names short.
* Use the same names across all figures.
* Put legend outside only when it blocks data.
* Use one shared legend for small multiples.

Recommended legend names:

```text
Baseline
Tuned
Ours
Oracle
Upper Bound
```

---

## 6. Error Bar Rules

Use error bars when repeated runs exist.

Preferred:

```python
ax.errorbar(x, mean, yerr=std, marker="o", capsize=2)
```

Allowed definitions:

```text
std
95% CI
min/max
p25/p75
```

Rules:

* State the error definition in caption or figure note.
* Do not show error bars if they make the figure unreadable.
* For latency distributions, prefer percentile bars or CDF.

---

## 7. Normalization Rules

Use normalized values when absolute values are less important than relative comparison.

Good labels:

```text
Normalized Runtime
Normalized Throughput
Speedup over Baseline
Relative Memory Usage
```

Rules:

* Always state the normalization baseline.
* Use `1.0x` as the baseline reference.
* Add a horizontal reference line at `1.0`.

Example:

```python
ax.axhline(1.0, color=COLORS["upper_bound"], linestyle="--", linewidth=1.0)
ax.set_ylabel("Normalized Runtime")
```

---

## 8. CDF / Distribution Rules

Use CDF when tail behavior matters.

Recommended for:

* latency
* response time
* error distribution
* request-level metrics
* file size distribution
* task duration

Style:

```python
ax.plot(sorted_values, cdf_values, color=COLORS["ours"], label="Ours")
ax.set_xlabel("Latency (ms)")
ax.set_ylabel("CDF")
ax.set_ylim(0, 1.0)
```

Rules:

* Use CDF for full distribution.
* Use box plot only for compact summaries.
* Use percentile bar when only P50/P95/P99 matter.

---

## 9. Caption Template

Use this format outside the figure.

```text
Figure X: [Metric] under [main varying factor].
The x-axis shows [variable]. The y-axis shows [metric and unit].
We compare [methods]. Higher/lower is better.
Error bars show [definition].
```

Example:

```text
Figure X: Normalized runtime under different input sizes.
The x-axis shows input size. The y-axis shows runtime normalized to Baseline.
Lower is better. Error bars show standard deviation over three runs.
```

---

## 10. Code Generation Checklist

Before generating matplotlib code, verify:

* [ ] All figure text is English.
* [ ] One figure answers one question.
* [ ] One y-axis is used.
* [ ] Units are included in axis labels.
* [ ] Method colors are consistent.
* [ ] `Ours` is visually highlighted.
* [ ] Upper bound uses black dashed line.
* [ ] No 3D chart.
* [ ] No gradient background.
* [ ] No unnecessary annotations.
* [ ] Figure is saved as PDF and PNG.
* [ ] `bbox_inches="tight"` is used.
* [ ] `pdf.fonttype=42` is set.

