---
name: C Performance Analysis
description: CPU profiling, memory analysis, benchmarking, and optimization for Linux C/C++ applications. Use when C code is slow, memory usage is high, or optimization is needed.
allowed-tools: Bash, Read, Grep, Glob

---

# C Performance Analysis and Optimization

**Version**: 1.0.0
**Last Updated**: 2026-05-17
**Priority**: ⭐⭐⭐ (P2 Level)
**Purpose**: Linux C/C++ 应用程序的性能分析与优化

---

## Overview

针对 Linux 平台上的 C/C++ 应用程序，提供从数据采集、热点定位、瓶颈分析到优化建议的完整性能分析工作流。支持 CPU、内存、缓存、I/O 等多维度分析。

---

## Trigger

| 触发词       | 示例                                      |
| ------------ | ----------------------------------------- |
| 运行缓慢     | "this C program is slow"                  |
| 内存使用     | "why is memory usage so high?"            |
| 优化         | "optimize this function"                  |
| 性能分析     | "profile this C code"                     |
| 内存泄漏     | "there's a memory leak"                   |
| 基准测试     | "benchmark performance"                   |
| 缓存未命中   | "cache miss rate is high"                 |
| pprof        | "analyze this .pb.gz profile"             |

---

## Tool Matrix

### 核心工具优先级

| 优先级 | 工具              | 用途             | 类型   | 命令                            |
| ------ | ----------------- | ---------------- | ------ | ------------------------------- |
| 1      | `perf`            | CPU/缓存/全系统  | 采样   | `perf record -g ./binary`      |
| 2      | `gperftools`      | CPU/Heap (pprof) | 采样   | `CPUPROFILE=cpu.pb.gz ./binary` |
| 3      | `valgrind/callgrind` | CPU调用图     | 模拟   | `valgrind --tool=callgrind`    |
| 4      | `valgrind/massif` | 堆内存           | 模拟   | `valgrind --tool=massif`       |
| 5      | `valgrind/memcheck` | 内存泄漏       | 模拟   | `valgrind --tool=memcheck`     |
| 6      | `heaptrack`       | 堆追踪           | 采样   | `heaptrack ./binary`           |
| 7      | `perf-skill`      | pprof分析输出    | 转换   | `npx perf-skill analyze`       |
| 8      | `strace`          | 系统调用         | 追踪   | `strace -c ./binary`           |
| 9      | `latencytop`      | 延迟分析         | 观察   | `latencytop`                   |
| 10     | `bpftrace/eBPF`   | 动态追踪         | 追踪   | `bpftrace -e 'profile:... {}'` |

### 工具选择决策树

```
性能问题？
├── CPU 热点？
│   ├── 需要低开销？ → perf record（采样，<5% 开销）
│   ├── 需要 pprof 格式？ → gperftools + perf-skill
│   └── 需要精确调用图？ → callgrind（高开销，~20x 慢）
├── 内存问题？
│   ├── 泄漏？ → valgrind --tool=memcheck
│   ├── 堆使用量？ → valgrind --tool=massif 或 heaptrack
│   └── 需要 pprof 格式？ → gperftools heap-profiler + perf-skill
├── 缓存问题？
│   ├── L1/L2 miss？ → perf stat -e cache-misses,cache-references
│   └── TLB miss？ → perf stat -e dTLB-load-misses
├── I/O 瓶颈？
│   ├── 系统调用？ → strace -c
│   └── 文件 I/O？ → perf record -e syscalls:sys_enter_read
└── 动态追踪？
    └── 生产环境低开销？ → bpftrace/eBPF
```

---

## Analysis Patterns

### Pattern 1: perf — CPU 性能分析

#### 1.1 基本采样

```bash
# 编译时加 -g 保留符号信息（必须！）
gcc -O2 -g -o myapp main.c

# 采样记录（推荐频率 999Hz，避免与定时器共振）
perf record -F 999 -g -- ./myapp [args]

# 查看报告
perf report

# 直接统计（无需交互）
perf report --stdio
```

#### 1.2 火焰图生成

```bash
# 方法A: 使用 FlameGraph 脚本（ Brendan Gregg ）
git clone https://github.com/brendangregg/FlameGraph /tmp/FlameGraph
perf record -F 999 -g -- ./myapp
perf script | /tmp/FlameGraph/stackcollapse-perf.pl | /tmp/FlameGraph/flamegraph.pl > flamegraph.svg

# 方法B: 使用 perf report 的火焰图模式（Linux 5.8+）
perf record -F 999 -g -- ./myapp
perf report --hierarchy --stdio

# 方法C: 使用 inferno（Rust 实现，更快）
cargo install inferno
perf record -F 999 -g -- ./myapp
perf script | inferno-collapse-perf | inferno-flamegraph > flamegraph.svg
```

#### 1.3 缓存分析

```bash
# 缓存命中率
perf stat -e cache-misses,cache-references,L1-dcache-load-misses,L1-dcache-loads ./myapp

# TLB 未命中
perf stat -e dTLB-load-misses,dTLB-loads,iTLB-load-misses,iTLB-loads ./myapp

# 分支预测失败
perf stat -e branch-misses,branches ./myapp
```

#### 1.4 附加到运行中进程

```bash
# 附加到 PID，采集 30 秒
perf record -F 999 -g -p <PID> -- sleep 30

# 系统级采样（所有 CPU）
perf record -F 999 -ag -- sleep 10
```

#### 1.5 perf stat 宏观概览

```bash
# 快速性能概览
perf stat ./myapp

# 详细硬件事件
perf stat -d ./myapp

# 自定义事件
perf stat -e cycles,instructions,cache-misses,branch-misses ./myapp
```

---

### Pattern 2: gperftools — pprof 格式分析

#### 2.1 安装

```bash
# Ubuntu/Debian
sudo apt install google-perftools libgoogle-perftools-dev

# CentOS/RHEL
sudo yum install gperftools gperftools-devel

# 从源码
git clone https://github.com/gperftools/gperftools
cd gperftools && cmake . && make && sudo make install
```

#### 2.2 CPU Profiling

```c
// 方式A: 代码插桩
#include <gperftools/profiler.h>

int main() {
    ProfilerStart("cpu_profile.pb.gz");
    // ... 你的代码 ...
    ProfilerStop();
    return 0;
}
```

```bash
# 编译并链接
gcc -O2 -g -o myapp main.c -lprofiler

# 方式B: 环境变量（无需修改代码）
CPUPROFILE=cpu_profile.pb.gz LD_PRELOAD=/usr/lib/libprofiler.so ./myapp
```

#### 2.3 Heap Profiling

```c
// 方式A: 代码插桩
#include <gperftools/heap-profiler.h>

int main() {
    HeapProfilerStart("heap_profile");
    // ... 你的代码 ...
    HeapProfilerStop();
    return 0;
}
```

```bash
# 编译并链接
gcc -O2 -g -o myapp main.c -ltcmalloc

# 方式B: 环境变量
HEAPPROFILE=heap_profile LD_PRELOAD=/usr/lib/libtcmalloc.so ./myapp
```

#### 2.4 Heap Checker（内存泄漏检测）

```c
#include <gperftools/heap-checker.h>

int main() {
    HeapLeakChecker checker("my_check");
    // ... 你的代码 ...
    if (!checker.NoLeaks()) {
        fprintf(stderr, "Memory leaks detected!\n");
    }
    return 0;
}
```

```bash
# 编译并运行
gcc -O2 -g -o myapp main.c -ltcmalloc
HEAPCHECK=normal ./myapp    # normal / strict / draconian
```

#### 2.5 pprof 可视化

```bash
# 命令行文本分析
pprof --text ./myapp cpu_profile.pb.gz

# 生成火焰图（SVG）
pprof --svg ./myapp cpu_profile.pb.gz > flamegraph.svg

# 生成调用图（PNG）
pprof --png ./myapp cpu_profile.pb.gz > callgraph.png

# Web 界面（交互式）
pprof --http=:8080 ./myapp cpu_profile.pb.gz

# 对比两个 profile
pprof --base=before.pb.gz ./myapp after.pb.gz --text
```

#### 2.6 接入 perf-skill 生成结构化报告

```bash
# 生成 .pb.gz 后用 perf-skill 分析
npx perf-skill analyze cpu_profile.pb.gz -o analysis.md -j results.json

# 对比修改前后
npx perf-skill diff before.pb.gz after.pb.gz -o diff.md -j diff.json

# Heap 分析
npx perf-skill analyze heap_profile.0001.pb.gz -t heap -o heap.md
```

---

### Pattern 3: Valgrind — 内存与调用图分析

#### 3.1 Memcheck（内存泄漏检测）

```bash
# 基本内存检查
valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all \
         --track-origins=yes --verbose ./myapp

# 生成抑制文件（忽略第三方库的误报）
valgrind --gen-suppressions=all --tool=memcheck ./myapp

# 使用抑制文件
valgrind --suppressions=myapp.supp --tool=memcheck ./myapp
```

#### 3.2 Callgrind（调用图分析）

```bash
# 生成调用图数据
valgrind --tool=callgrind ./myapp

# 只追踪特定函数
valgrind --tool=callgrind --toggle-collect=process_data* ./myapp

# 使用 KCachegrind 可视化
kcachegrind callgrind.out.*

# 命令行查看
callgrind_annotate callgrind.out.*
```

#### 3.3 Massif（堆内存分析）

```bash
# 堆内存分析
valgrind --tool=massif --stacks=yes ./myapp

# 查看结果
ms_print massif.out.*

# 使用 massif-visualizer（GUI）
massif-visualizer massif.out.*
```

#### 3.4 Cachegrind（缓存模拟）

```bash
# 缓存命中率模拟
valgrind --tool=cachegrind ./myapp

# 查看结果
cg_annotate cachegrind.out.*

# 指定缓存参数（模拟不同 CPU）
valgrind --tool=cachegrind --I1=32768,8,64 --D1=32768,8,64 --LL=8388608,16,64 ./myapp
```

#### 3.5 DRD / Helgrind（多线程检测）

```bash
# 数据竞争检测
valgrind --tool=helgrind ./myapp

# DRD（更快的竞争检测）
valgrind --tool=drd ./myapp
```

---

### Pattern 4: heaptrack — 堆内存追踪

```bash
# 安装
sudo apt install heaptrack heaptrack-gui

# 运行
heaptrack ./myapp

# 分析结果（命令行）
heaptrack_print heaptrack.myapp.*.gz

# 分析结果（GUI）
heaptrack_gui heaptrack.myapp.*.gz

# 附加到运行中进程
heaptrack -p <PID>
```

---

### Pattern 5: eBPF/bpftrace — 动态追踪

```bash
# 安装
sudo apt install bpftrace

# CPU 采样（低开销，适合生产环境）
bpftrace -e 'profile:hz:999 /pid == <PID>/ { @[ustack] = count(); }'

# 追踪特定函数耗时
bpftrace -e 'uprobe:/path/to/myapp:process_data { @start[tid] = nsecs; }
             uretprobe:/path/to/myapp:process_data /@start[tid]/ {
                 @latency = hist(nsecs - @start[tid]);
                 delete(@start[tid]);
             }'

# 追踪内存分配
bpftrace -e 'uprobe:libc:malloc { @size = hist(arg0); }'

# 追踪系统调用
bpftrace -e 'tracepoint:syscalls:sys_enter_read { @reads[pid, comm] = count(); }'
```

---

### Pattern 6: strace — 系统调用分析

```bash
# 系统调用统计
strace -c ./myapp

# 追踪特定系统调用
strace -e trace=read,write,open,close ./myapp

# 追踪网络相关
strace -e trace=network ./myapp

# 追踪信号
strace -e trace=signal ./myapp

# 附加到运行中进程
strace -p <PID> -c
```

---

### Pattern 7: Benchmarking（基准测试）

#### 7.1 微基准测试

```c
// bench_timer.c
#include <stdio.h>
#include <time.h>

#define BENCH_ITER 1000000

int main() {
    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < BENCH_ITER; i++) {
        // 待测代码
        my_function(i);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("Total: %.6f s\n", elapsed);
    printf("Per iteration: %.2f ns\n", elapsed / BENCH_ITER * 1e9);
    return 0;
}
```

#### 7.2 使用 Google Benchmark

```cpp
// bench_myapp.cpp
#include <benchmark/benchmark.h>

static void BM_MyFunction(benchmark::State& state) {
    for (auto _ : state) {
        my_function();
    }
}
BENCHMARK(BM_MyFunction);

BENCHMARK_MAIN();
```

```bash
# 安装
sudo apt install libbenchmark-dev

# 编译
g++ -O2 -o bench_myapp bench_myapp.cpp -lbenchmark -lpthread

# 运行
./bench_myapp
```

---

## Optimization Strategies

### 优化优先级

| 优先级 | 策略                | 效果 | 难度 | 典型场景                   |
| ------ | ------------------- | ---- | ---- | -------------------------- |
| 1      | 算法改进            | 高   | 中   | O(n²) → O(n log n)        |
| 2      | 数据结构变更        | 高   | 中   | 链表 → 数组，哈希 → B树   |
| 3      | 减少内存分配        | 中   | 低   | 预分配、对象池、栈替代堆  |
| 4      | 缓存友好           | 中   | 中   | 数据局部性、结构体重排     |
| 5      | 并行化（多线程）    | 中   | 高   | OpenMP、pthreads、C11 threads |
| 6      | I/O 优化            | 中   | 中   | 批量读写、mmap、异步I/O   |
| 7      | 编译器优化选项      | 低   | 低   | -O3, -march=native, LTO   |
| 8      | SIMD/向量化         | 低   | 高   | AVX2/AVX-512 intrinsics   |
| 9      | 内联汇编            | 低   | 高   | 特定热点函数               |

### 常见优化示例

#### 减少内存分配

```c
// ❌ 循环中反复分配
for (int i = 0; i < n; i++) {
    char *buf = malloc(1024);
    process(buf, i);
    free(buf);
}

// ✅ 预分配复用
char *buf = malloc(1024);
for (int i = 0; i < n; i++) {
    process(buf, i);
}
free(buf);
```

#### 缓存友好 — 结构体重排

```c
// ❌ 冷热数据混杂（缓存行浪费）
struct Person {
    char name[64];     // 冷数据
    int age;           // 热数据
    char address[128]; // 冷数据
    float score;       // 热数据
};

// ✅ 热数据分离（提高缓存命中率）
struct PersonHot {
    int age;
    float score;
};

struct PersonCold {
    char name[64];
    char address[128];
};
```

#### 减少间接访问

```c
// ❌ 指针链（多次内存访问）
for (int i = 0; i < n; i++) {
    total += nodes[i]->next->value;
}

// ✅ 数据平坦化（连续内存）
int *values = malloc(n * sizeof(int));
for (int i = 0; i < n; i++) {
    values[i] = nodes[i]->next->value;
}
for (int i = 0; i < n; i++) {
    total += values[i];
}
```

#### 避免分支预测失败

```c
// ❌ 不可预测的分支
if (random_condition) {
    do_a();
} else {
    do_b();
}

// ✅ 使用条件传送或查找表
// 编译器可能自动优化为 cmov
result = condition ? a : b;

// 查找表替代 switch
static const int lookup[] = {val0, val1, val2, val3};
result = lookup[index];
```

---

## Compilation for Profiling

### 编译选项对照

```bash
# 基本调试信息（用于符号解析）
gcc -g -O2 -o myapp main.c

# 详细调试信息
gcc -g3 -O2 -o myapp main.c

# 保留帧指针（火焰图需要，禁用帧指针省略）
gcc -g -O2 -fno-omit-frame-pointer -o myapp main.c

# 链接时优化（LTO）
gcc -g -O2 -flto -o myapp main.c

# PGO 编译（详见下方）

# 生成独立调试符号文件
objcopy --only-keep-debug myapp myapp.debug
strip --strip-debug myapp
objcopy --add-gnu-debuglink=myapp.debug myapp
```

---

## PGO (Profile-Guided Optimization)

```bash
# Step 1: 插桩编译
gcc -fprofile-generate=/tmp/pgo_data -O2 -g -fno-omit-frame-pointer -o myapp_pgo main.c

# Step 2: 运行典型负载收集 profile
./myapp_pgo [typical workload]

# Step 3: 使用 profile 重新编译
gcc -fprofile-use=/tmp/pgo_data -O2 -g -fno-omit-frame-pointer -o myapp main.c

# 清理 profile 数据
rm -rf /tmp/pgo_data
```

---

## Performance Targets

| 指标         | 目标        | 测量方法                          |
| ------------ | ----------- | --------------------------------- |
| 缓存命中率   | >95%        | `perf stat -e cache-misses`      |
| L1 D-Cache   | <5% miss    | `perf stat -e L1-dcache-load-misses` |
| 分支预测     | <2% miss    | `perf stat -e branch-misses`     |
| 内存泄漏     | 0           | `valgrind --tool=memcheck`       |
| 二进制大小   | 按项目约定   | `size myapp` / `nm -S myapp`    |
| 最大堆使用   | 按项目约定   | `valgrind --tool=massif`         |
| 页错误       | 最小化      | `/usr/bin/time -v ./myapp`       |

---

## Complete Analysis Workflow

### 标准流程

```
Step 1: 编译
    gcc -O2 -g -fno-omit-frame-pointer -o myapp main.c

Step 2: 宏观概览
    perf stat -d ./myapp
    → 识别: CPU bound / Memory bound / I/O bound

Step 3: 热点定位
    perf record -F 999 -g -- ./myapp
    perf report --stdio
    → 识别: 前3个热点函数

Step 4: 火焰图可视化
    perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
    → 识别: 调用路径和占比

Step 5: 内存检查
    valgrind --tool=memcheck --leak-check=full ./myapp
    → 确认: 无内存泄漏

Step 6: 堆分析（如内存占用高）
    valgrind --tool=massif ./myapp
    ms_print massif.out.*
    → 识别: 堆内存增长点和峰值

Step 7: 缓存分析（如缓存问题）
    perf stat -e cache-misses,cache-references,L1-dcache-load-misses ./myapp
    → 识别: 缓存命中率

Step 8: 优化实施
    根据分析结果，按优化优先级实施

Step 9: 验证改善
    perf-skill diff before.pb.gz after.pb.gz
    或对比 perf stat 数据
```

### gperftools + perf-skill 流程

```
Step 1: 编译
    gcc -O2 -g -o myapp main.c -lprofiler -ltcmalloc

Step 2: 采集 CPU profile
    CPUPROFILE=cpu.pb.gz ./myapp

Step 3: perf-skill 分析
    npx perf-skill analyze cpu.pb.gz -o analysis.md -j results.json

Step 4: 阅读分析结果，生成优化建议

Step 5: 实施优化

Step 6: 重新采集
    CPUPROFILE=cpu_after.pb.gz ./myapp

Step 7: 对比
    npx perf-skill diff cpu.pb.gz cpu_after.pb.gz -o diff.md
```

---

## WSL2 Specific Notes

### perf 内核版本不匹配

WSL2 的内核版本通常与安装的 linux-tools 包不一致，导致 `perf` 命令报错。

```bash
# 查看实际安装的 perf 路径
find /usr/lib/linux-tools/ -name "perf" 2>/dev/null
# 典型输出: /usr/lib/linux-tools/5.15.0-179-generic/perf

# 使用完整路径运行
/usr/lib/linux-tools/<version>/perf record -F 999 -g -- ./myapp
/usr/lib/linux-tools/<version>/perf report --stdio
```

### perf 硬件事件不可用

WSL2 中 `perf stat -d` 的硬件事件（cache-misses, instructions 等）通常返回 "not supported"。
但 `perf record` 和 `perf report` 的软件采样仍然可用。

```bash
# ❌ WSL2 中硬件事件不可用
perf stat -d ./myapp  # "not supported" errors

# ✅ 软件采样仍然有效
perf record -F 999 -g -- ./myapp
perf report --stdio
```

### gperftools pprof 二进制名称

Ubuntu/Debian 上 gperftools 的 pprof 命令名为 `google-pprof`，不是 `pprof`：

```bash
# Ubuntu/Debian
google-pprof --text ./myapp cpu_profile.pb.gz

# 其他发行版或手动安装
pprof --text ./myapp cpu_profile.pb.gz
```

### HEAPPROFILE 需要链接 tcmalloc

Heap profiling 使用 `HEAPPROFILE` 环境变量时，必须链接 `libtcmalloc`（不是 `libprofiler`）：

```bash
# ❌ 错误: -lprofiler 只支持 CPU profiling
gcc -O2 -g -o myapp main.c -lprofiler

# ✅ 正确: -ltcmalloc 支持 heap profiling
gcc -O2 -g -o myapp main.c -ltcmalloc
HEAPPROFILE=heap_profile ./myapp
```

### npx perf-skill 在 WSL 中可能超时

`npx perf-skill analyze` 需要网络下载包，在 WSL 中可能因网络问题超时。
可改用 `google-pprof` 直接分析：

```bash
# 替代方案: 直接用 pprof 分析
google-pprof --text ./myapp cpu_profile.pb.gz
google-pprof --svg ./myapp cpu_profile.pb.gz > flamegraph.svg
```

### FlameGraph 生成可能因网络超时

`git clone https://github.com/brendangregg/FlameGraph` 在 WSL 中可能因网络问题失败。
替代方案：使用 `perf report --stdio` 的文字输出，或使用 inferno（Rust 实现，cargo install）。

---

## Troubleshooting

### perf 权限问题

```bash
# 临时解决
sudo sysctl -w kernel.perf_event_parity=1
sudo sysctl -w kernel.kptr_restrict=0

# 永久解决
echo "kernel.perf_event_parity=1" | sudo tee -a /etc/sysctl.d/99-perf.conf
echo "kernel.kptr_restrict=0" | sudo tee -a /etc/sysctl.d/99-perf.conf
```

### 符号信息缺失

```bash
# 确认二进制有符号
file myapp              # 应包含 "not stripped"
nm myapp | head         # 应有函数名
readelf -S myapp | grep debug  # 应有 .debug_* 段

# 安装系统库调试符号
sudo apt install libc6-dbg
# CentOS
sudo debuginfo-install glibc
```

### gperftools 链接错误

```bash
# 找到库路径
ldconfig -p | grep profiler
ldconfig -p | grep tcmalloc

# 指定库路径
gcc -O2 -g -o myapp main.c -L/usr/local/lib -lprofiler -Wl,-rpath,/usr/local/lib
```

### Valgrind 误报过多

```bash
# 使用抑制文件
valgrind --suppressions=/usr/lib/valgrind/default.supp --tool=memcheck ./myapp

# 生成自定义抑制
valgrind --gen-suppressions=yes --tool=memcheck ./myapp 2>&1 | grep -A 10 "suppression"
```

### 火焰图显示 [unknown]

```bash
# 原因: 帧指针省略（-fomit-frame-pointer）
# 解决: 编译时加 -fno-omit-frame-pointer

# 或使用 DWARF 展开
perf record -F 999 --call-graph dwarf -- ./myapp
```

---

## Success Criteria

| 检查项       | 标准                       |
| ------------ | -------------------------- |
| 瓶颈识别     | 定位前3个热点              |
| 基准测试     | 优化前后数据对比           |
| 内存泄漏     | valgrind 报告 0 leak       |
| 缓存命中率   | >95%                       |
| 分支预测     | <2% miss rate              |
| 回归测试     | 功能正确，性能维持         |

---

## Related Skills

- **performance-analysis**: Rust 应用性能分析
- **perf-skill**: pprof .pb.gz 文件分析与对比
- **systematic-debugging**: 系统化调试流程
- **Security Audit**: 性能与安全的权衡