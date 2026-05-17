# C 性能分析实战报告

## 项目: perf-demo (~/projects/perf-demo)

---

## 1. 示例程序说明

`perf_demo.c` 故意包含 6 种典型性能问题:

| # | 问题 | 代码位置 | 影响 |
|---|------|----------|------|
| 1 | 链表遍历 (缓存不友好) | `sum_linked_list()` | 指针追逐，L1 cache miss 高 |
| 2 | O(n²) 冒泡排序 | `bubble_sort()` | n=50000 时耗时 ~2s |
| 3 | 循环中反复 malloc/free | `process_strings()` | 堆分配开销 + 内存碎片 |
| 4 | 重复调用 strlen | `count_long_names()` | 同一字符串计算多次 |
| 5 | 内存泄漏 | `leak_memory()` | 1MB 忘记 free |
| 6 | 链表 vs 数组对比 | main() 第1段 | 缓存局部性差异 |

---

## 2. 分析过程与结果

### 2.1 perf — CPU 热点定位

```bash
# 编译 (必须 -g + -fno-omit-frame-pointer)
gcc -O2 -g -fno-omit-frame-pointer -o perf_demo perf_demo.c

# 采样
perf record -F 999 -g -- ./perf_demo

# 报告
perf report --stdio
```

**关键发现: bubble_sort 占 99.46% CPU 时间**

```
Overhead  Command     Object      Symbol
  99.46%  perf_demo   perf_demo   [.] bubble_sort
   0.19%  perf_demo   perf_demo   [.] process_strings
   0.12%  perf_demo   perf_demo   [.] build_linked_list
```

结论: 排序是绝对瓶颈，算法优化为第一优先级。

---

### 2.2 gperftools — pprof 格式分析

```bash
# CPU profile (环境变量方式，无需修改代码)
CPUPROFILE=cpu_profile.pb.gz LD_PRELOAD=/lib/x86_64-linux-gnu/libprofiler.so ./perf_demo

# 文本分析
google-pprof --text ./perf_demo cpu_profile.pb.gz
```

**CPU profile 结果:**
```
Total: 2.0s
  97.4%  97.4%  bubble_sort
   1.0%  98.4%  process_strings
   0.5%  98.9%  build_linked_list
```

**Heap profile 结果 (HEAPPROFILE + tcmalloc):**
```
Total: 1.0 MB
  99.6%  snprintf (via leak_memory)    ← 1MB 泄漏
```

gperftools 同样确认 bubble_sort 是主要热点，同时 heap profile 精准定位了
leak_memory 中的 1MB 泄漏。

---

### 2.3 Valgrind memcheck — 内存泄漏检测

```bash
valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all \
         --track-origins=yes ./perf_demo
```

**关键输出:**
```
HEAP SUMMARY:
    in use at exit: 1,048,576 bytes in 1 blocks
    total heap usage: 100,005 allocs, 100,004 frees

1,048,576 bytes in 1 blocks are definitely lost
   at 0x4848899: malloc
   by 0x109AB1: leak_memory (perf_demo.c:124)    ← 精准定位行号
   by 0x109564: main (perf_demo.c:186)

LEAK SUMMARY:
   definitely lost: 1,048,576 bytes in 1 blocks   ← 确认泄漏
```

结论: 1MB 内存泄漏，精确到源码第 124 行 leak_memory() 中的 malloc。

---

### 2.4 Valgrind massif — 堆内存分析

```bash
valgrind --tool=massif --stacks=yes ./perf_demo
ms_print massif.out.*
```

**堆内存峰值 18.55 MB，主要分配来源:**

| 函数 | 占比 | 用途 |
|------|------|------|
| process_strings (malloc 256B) | 65.8% | 12.8MB — 循环中小块分配 |
| create_node (链表节点) | 12.3% | 2.4MB |
| main (Item 数组) | 9.3% | 1.8MB |
| leak_memory (泄漏) | 5.4% | 1.0MB |

结论: process_strings 的循环 malloc 是堆内存主要消费者，应预分配。

---

## 3. 优化实施

### 优化 1: 链表 → 数组 (缓存友好)

```c
// ❌ Before: 链表遍历 (指针追逐，缓存不友好)
long long sum_linked_list(Node *head) {
    while (head) { total += head->value; head = head->next; }
}

// ✅ After: 数组遍历 (连续内存，缓存友好)
long long sum_array_opt(ItemOpt *items, int size) {
    for (int i = 0; i < size; i++) { total += items[i].value; }
}
```

### 优化 2: 冒泡排序 → qsort (O(n²) → O(n log n))

```c
// ❌ Before: O(n²)
bubble_sort(sort_arr, size);        // 50000 items → 2.0s

// ✅ After: O(n log n)
qsort(sort_arr, size, sizeof(int), cmp_int);  // 50000 items → 0.003s
```

### 优化 3: 循环 malloc → 预分配池

```c
// ❌ Before: 每次循环 malloc
for (int i = 0; i < count; i++) {
    char *buf = malloc(256);
    snprintf(buf, 256, "result_%d", i);
    results[i] = buf;
}

// ✅ After: 一次分配大缓冲区
sp->pool = malloc(count * BUF_SIZE);  // 一次性
for (int i = 0; i < count; i++) {
    snprintf(sp->pool + i * BUF_SIZE, BUF_SIZE, "result_%d", i);
}
```

### 优化 4: 缓存 strlen 结果

```c
// ❌ Before: 同一字符串计算两次
if (strlen(s) > 20) { ... }
if (strlen(s) > 10) { ... }  // 重复计算

// ✅ After: 缓存结果
size_t len = strlen(s);
if (len > 20) { ... }
```

### 优化 5: 修复内存泄漏

```c
// ❌ Before: 忘记 free
void leak_memory(void) {
    char *leaked = malloc(1024 * 1024);
    printf("%s", leaked);
    // 没有 free!
}

// ✅ After: 正确释放
void no_leak_memory(void) {
    char *buf = malloc(1024 * 1024);
    printf("%s", buf);
    free(buf);  // ✅
}
```

---

## 4. 性能对比

### 运行时间对比 (n=50000)

| 项目 | Before | After | 加速比 |
|------|--------|-------|--------|
| 数据结构遍历 | 0.0030s (链表) | 0.0020s (数组) | 1.5x |
| 排序 | 2.0250s (冒泡) | 0.0031s (qsort) | **653x** |
| 字符串处理 | 0.0047s (循环malloc) | 0.0040s (预分配) | 1.2x |
| strlen | 0.0005s (重复) | 0.0004s (缓存) | 1.3x |
| **总计** | **2.034s** | **0.0095s** | **214x** |

### 内存泄漏对比

| 指标 | Before | After |
|------|--------|-------|
| Valgrind 错误数 | 1 (definitely lost: 1MB) | **0** |
| 泄漏字节数 | 1,048,576 | **0** |
| allocs/frees | 100,005 / 100,004 | 8 / 8 (全部释放) |
| 结论 | "definitely lost" | **"no leaks are possible"** |

---

## 5. 工具使用总结

| 工具 | 用途 | 开销 | 本例发现 |
|------|------|------|----------|
| perf record + report | CPU 热点定位 | <5% | bubble_sort 99.46% |
| gperftools CPU profiler | pprof 格式 CPU 分析 | ~1% | 同上，97.4% |
| gperftools heap profiler | 堆分配追踪 | ~1% | leak_memory 1MB 泄漏 |
| valgrind memcheck | 内存泄漏检测 | ~20x 慢 | 精准定位泄漏行号 |
| valgrind massif | 堆内存增长分析 | ~10x 慢 | 峰值 18.55MB，process_strings 占 65% |

### 工具选择建议

- **快速定位 CPU 瓶颈** → perf (低开销，首选)
- **需要 pprof 格式 / 火焰图** → gperftools
- **内存泄漏** → valgrind memcheck (最精确)
- **堆内存增长** → valgrind massif 或 gperftools heap
- **生产环境低开销** → bpftrace/eBPF

---

## 6. 文件清单

```
~/projects/perf-demo/
├── perf_demo.c              # 原始版 (含性能问题)
├── perf_demo_optimized.c    # 优化版
├── perf_demo                # 原始二进制
├── perf_demo_optimized      # 优化二进制
├── perf_demo_tc             # tcmalloc 链接版
├── perf.data                # perf 采样数据
├── cpu_profile.pb.gz        # gperftools CPU profile
├── heap_profile.0001.heap   # gperftools heap profile
├── callgraph.svg            # pprof 调用图 (SVG)
└── massif.out.*             # massif 堆内存数据
```
