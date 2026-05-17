     1|# C 性能分析实战报告
     2|
     3|## 项目: perf-demo (~/projects/perf-demo)
     4|
     5|---
     6|
     7|## 1. 示例程序说明
     8|
     9|`perf_demo.c` 故意包含 6 种典型性能问题:
    10|
    11|| # | 问题 | 代码位置 | 影响 |
    12||---|------|----------|------|
    13|| 1 | 链表遍历 (缓存不友好) | `sum_linked_list()` | 指针追逐，L1 cache miss 高 |
    14|| 2 | O(n²) 冒泡排序 | `bubble_sort()` | n=50000 时耗时 ~2s |
    15|| 3 | 循环中反复 malloc/free | `process_strings()` | 堆分配开销 + 内存碎片 |
    16|| 4 | 重复调用 strlen | `count_long_names()` | 同一字符串计算多次 |
    17|| 5 | 内存泄漏 | `leak_memory()` | 1MB 忘记 free |
    18|| 6 | 链表 vs 数组对比 | main() 第1段 | 缓存局部性差异 |
    19|
    20|---
    21|
    22|## 2. 分析过程与结果
    23|
    24|### 2.1 perf — CPU 热点定位
    25|
    26|```bash
    27|# 编译 (必须 -g + -fno-omit-frame-pointer)
    28|gcc -O2 -g -fno-omit-frame-pointer -o perf_demo perf_demo.c
    29|
    30|# 采样
    31|perf record -F 999 -g -- ./perf_demo
    32|
    33|# 报告
    34|perf report --stdio
    35|```
    36|
    37|**关键发现: bubble_sort 占 99.46% CPU 时间**
    38|
    39|```
    40|Overhead  Command     Object      Symbol
    41|  99.46%  perf_demo   perf_demo   [.] bubble_sort
    42|   0.19%  perf_demo   perf_demo   [.] process_strings
    43|   0.12%  perf_demo   perf_demo   [.] build_linked_list
    44|```
    45|
    46|结论: 排序是绝对瓶颈，算法优化为第一优先级。
    47|
    48|---
    49|
    50|### 2.2 gperftools — pprof 格式分析
    51|
    52|```bash
    53|# CPU profile (环境变量方式，无需修改代码)
    54|CPUPROFILE=cpu_profile.pb.gz LD_PRELOAD=/lib/x86_64-linux-gnu/libprofiler.so ./perf_demo
    55|
    56|# 文本分析
    57|google-pprof --text ./perf_demo cpu_profile.pb.gz
    58|```
    59|
    60|**CPU profile 结果:**
    61|```
    62|Total: 2.0s
    63|  97.4%  97.4%  bubble_sort
    64|   1.0%  98.4%  process_strings
    65|   0.5%  98.9%  build_linked_list
    66|```
    67|
    68|**Heap profile 结果 (HEAPPROFILE + tcmalloc):**
    69|```
    70|Total: 1.0 MB
    71|  99.6%  snprintf (via leak_memory)    ← 1MB 泄漏
    72|```
    73|
    74|gperftools 同样确认 bubble_sort 是主要热点，同时 heap profile 精准定位了
    75|leak_memory 中的 1MB 泄漏。
    76|
    77|---
    78|
    79|### 2.3 Valgrind memcheck — 内存泄漏检测
    80|
    81|```bash
    82|valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all \
    83|         --track-origins=yes ./perf_demo
    84|```
    85|
    86|**关键输出:**
    87|```
    88|HEAP SUMMARY:
    89|    in use at exit: 1,048,576 bytes in 1 blocks
    90|    total heap usage: 100,005 allocs, 100,004 frees
    91|
    92|1,048,576 bytes in 1 blocks are definitely lost
    93|   at 0x4848899: malloc
    94|   by 0x109AB1: leak_memory (perf_demo.c:124)    ← 精准定位行号
    95|   by 0x109564: main (perf_demo.c:186)
    96|
    97|LEAK SUMMARY:
    98|   definitely lost: 1,048,576 bytes in 1 blocks   ← 确认泄漏
    99|```
   100|
   101|结论: 1MB 内存泄漏，精确到源码第 124 行 leak_memory() 中的 malloc。
   102|
   103|---
   104|
   105|### 2.4 Valgrind massif — 堆内存分析
   106|
   107|```bash
   108|valgrind --tool=massif --stacks=yes ./perf_demo
   109|ms_print massif.out.*
   110|```
   111|
   112|**堆内存峰值 18.55 MB，主要分配来源:**
   113|
   114|| 函数 | 占比 | 用途 |
   115||------|------|------|
   116|| process_strings (malloc 256B) | 65.8% | 12.8MB — 循环中小块分配 |
   117|| create_node (链表节点) | 12.3% | 2.4MB |
   118|| main (Item 数组) | 9.3% | 1.8MB |
   119|| leak_memory (泄漏) | 5.4% | 1.0MB |
   120|
   121|结论: process_strings 的循环 malloc 是堆内存主要消费者，应预分配。
   122|
   123|---
   124|
   125|## 3. 优化实施
   126|
   127|### 优化 1: 链表 → 数组 (缓存友好)
   128|
   129|```c
   130|// ❌ Before: 链表遍历 (指针追逐，缓存不友好)
   131|long long sum_linked_list(Node *head) {
   132|    while (head) { total += head->value; head = head->next; }
   133|}
   134|
   135|// ✅ After: 数组遍历 (连续内存，缓存友好)
   136|long long sum_array_opt(ItemOpt *items, int size) {
   137|    for (int i = 0; i < size; i++) { total += items[i].value; }
   138|}
   139|```
   140|
   141|### 优化 2: 冒泡排序 → qsort (O(n²) → O(n log n))
   142|
   143|```c
   144|// ❌ Before: O(n²)
   145|bubble_sort(sort_arr, size);        // 50000 items → 2.0s
   146|
   147|// ✅ After: O(n log n)
   148|qsort(sort_arr, size, sizeof(int), cmp_int);  // 50000 items → 0.003s
   149|```
   150|
   151|### 优化 3: 循环 malloc → 预分配池
   152|
   153|```c
   154|// ❌ Before: 每次循环 malloc
   155|for (int i = 0; i < count; i++) {
   156|    char *buf = malloc(256);
   157|    snprintf(buf, 256, "result_%d", i);
   158|    results[i] = buf;
   159|}
   160|
   161|// ✅ After: 一次分配大缓冲区
   162|sp->pool = malloc(count * BUF_SIZE);  // 一次性
   163|for (int i = 0; i < count; i++) {
   164|    snprintf(sp->pool + i * BUF_SIZE, BUF_SIZE, "result_%d", i);
   165|}
   166|```
   167|
   168|### 优化 4: 缓存 strlen 结果
   169|
   170|```c
   171|// ❌ Before: 同一字符串计算两次
   172|if (strlen(s) > 20) { ... }
   173|if (strlen(s) > 10) { ... }  // 重复计算
   174|
   175|// ✅ After: 缓存结果
   176|size_t len = strlen(s);
   177|if (len > 20) { ... }
   178|```
   179|
   180|### 优化 5: 修复内存泄漏
   181|
   182|```c
   183|// ❌ Before: 忘记 free
   184|void leak_memory(void) {
   185|    char *leaked = malloc(1024 * 1024);
   186|    printf("%s", leaked);
   187|    // 没有 free!
   188|}
   189|
   190|// ✅ After: 正确释放
   191|void no_leak_memory(void) {
   192|    char *buf = malloc(1024 * 1024);
   193|    printf("%s", buf);
   194|    free(buf);  // ✅
   195|}
   196|```
   197|
   198|---
   199|
   200|## 4. 性能对比
   201|
   202|### 运行时间对比 (n=50000)
   203|
   204|| 项目 | Before | After | 加速比 |
   205||------|--------|-------|--------|
   206|| 数据结构遍历 | 0.0030s (链表) | 0.0020s (数组) | 1.5x |
   207|| 排序 | 2.0250s (冒泡) | 0.0031s (qsort) | **653x** |
   208|| 字符串处理 | 0.0047s (循环malloc) | 0.0040s (预分配) | 1.2x |
   209|| strlen | 0.0005s (重复) | 0.0004s (缓存) | 1.3x |
   210|| **总计** | **2.034s** | **0.0095s** | **214x** |
   211|
   212|### 内存泄漏对比
   213|
   214|| 指标 | Before | After |
   215||------|--------|-------|
   216|| Valgrind 错误数 | 1 (definitely lost: 1MB) | **0** |
   217|| 泄漏字节数 | 1,048,576 | **0** |
   218|| allocs/frees | 100,005 / 100,004 | 8 / 8 (全部释放) |
   219|| 结论 | "definitely lost" | **"no leaks are possible"** |
   220|
   221|---
   222|
   223|## 5. 工具使用总结
   224|
   225|| 工具 | 用途 | 开销 | 本例发现 |
   226||------|------|------|----------|
   227|| perf record + report | CPU 热点定位 | <5% | bubble_sort 99.46% |
   228|| gperftools CPU profiler | pprof 格式 CPU 分析 | ~1% | 同上，97.4% |
   229|| gperftools heap profiler | 堆分配追踪 | ~1% | leak_memory 1MB 泄漏 |
   230|| valgrind memcheck | 内存泄漏检测 | ~20x 慢 | 精准定位泄漏行号 |
   231|| valgrind massif | 堆内存增长分析 | ~10x 慢 | 峰值 18.55MB，process_strings 占 65% |
   232|
   233|### 工具选择建议
   234|
   235|- **快速定位 CPU 瓶颈** → perf (低开销，首选)
   236|- **需要 pprof 格式 / 火焰图** → gperftools
   237|- **内存泄漏** → valgrind memcheck (最精确)
   238|- **堆内存增长** → valgrind massif 或 gperftools heap
   239|- **生产环境低开销** → bpftrace/eBPF
   240|
   241|---
   242|
   243|## 6. 文件清单
   244|
   245|```
   246|~/projects/perf-demo/
   247|├── perf_demo.c              # 原始版 (含性能问题)
   248|├── perf_demo_optimized.c    # 优化版
   249|├── perf_demo                # 原始二进制
   250|├── perf_demo_optimized      # 优化二进制
   251|├── perf_demo_tc             # tcmalloc 链接版
   252|├── perf.data                # perf 采样数据
   253|├── cpu_profile.pb.gz        # gperftools CPU profile
   254|├── heap_profile.0001.heap   # gperftools heap profile
   255|├── callgraph.svg            # pprof 调用图 (SVG)
   256|└── massif.out.*             # massif 堆内存数据
   257|```
   258|