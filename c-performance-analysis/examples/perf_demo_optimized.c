     1|/*
     2| * perf_demo_optimized.c — 修复所有性能问题的优化版本
     3| *
     4| * 优化对照:
     5| *   1. 链表 → 数组 (缓存友好)
     6| *   2. 冒泡排序 O(n²) → qsort O(n log n)
     7| *   3. 循环中反复 malloc → 预分配大缓冲区
     8| *   4. 重复 strlen → 缓存长度
     9| *   5. 内存泄漏 → 修复 free
    10| */
    11|
    12|#include <stdio.h>
    13|#include <stdlib.h>
    14|#include <string.h>
    15|#include <time.h>
    16|
    17|#define DATA_SIZE 50000
    18|#define NAME_LEN 32
    19|#define BUF_SIZE 256
    20|
    21|/* ===== 优化1: 用数组替代链表 (缓存友好) ===== */
    22|typedef struct {
    23|    int value;
    24|    char name[NAME_LEN];
    25|    struct { int next; } link;  /* 用索引替代指针，数据连续 */
    26|} ItemOpt;
    27|
    28|long long sum_array_opt(ItemOpt *items, int size) {
    29|    long long total = 0;
    30|    for (int i = 0; i < size; i++) {
    31|        total += items[i].value;
    32|    }
    33|    return total;
    34|}
    35|
    36|/* ===== 优化2: qsort O(n log n) 替代冒泡排序 ===== */
    37|int cmp_int(const void *a, const void *b) {
    38|    return *(const int *)a - *(const int *)b;
    39|}
    40|
    41|/* ===== 优化3: 预分配缓冲区，避免循环中反复 malloc ===== */
    42|typedef struct {
    43|    char *pool;       /* 大缓冲区 */
    44|    int *offsets;     /* 每个字符串的偏移 */
    45|    int count;
    46|} StringPool;
    47|
    48|StringPool *process_strings_opt(int count) {
    49|    StringPool *sp = malloc(sizeof(StringPool));
    50|    sp->count = count;
    51|    sp->pool = malloc(count * BUF_SIZE);    /* 一次性分配 */
    52|    sp->offsets = malloc(count * sizeof(int));
    53|    for (int i = 0; i < count; i++) {
    54|        sp->offsets[i] = i * BUF_SIZE;
    55|        snprintf(sp->pool + sp->offsets[i], BUF_SIZE,
    56|                 "processed_result_%d_with_extra_padding_data", i);
    57|    }
    58|    return sp;
    59|}
    60|
    61|void string_pool_free(StringPool *sp) {
    62|    free(sp->pool);
    63|    free(sp->offsets);
    64|    free(sp);
    65|}
    66|
    67|/* ===== 优化4: 缓存 strlen 结果 ===== */
    68|int count_long_names_opt(StringPool *sp) {
    69|    int long_count = 0;
    70|    for (int i = 0; i < sp->count; i++) {
    71|        size_t len = strlen(sp->pool + sp->offsets[i]);  /* 只算一次 */
    72|        if (len > 20) long_count++;
    73|    }
    74|    return long_count;
    75|}
    76|
    77|/* ===== 优化5: 修复内存泄漏 ===== */
    78|void no_leak_memory(void) {
    79|    char *buf = malloc(1024 * 1024);
    80|    snprintf(buf, 64, "this memory is properly freed");
    81|    printf("  [safe ptr] %s\n", buf);
    82|    free(buf);  /* ✅ 正确释放 */
    83|}
    84|
    85|/* ===== 主程序 ===== */
    86|int main(int argc, char *argv[]) {
    87|    int size = DATA_SIZE;
    88|    if (argc > 1) size = atoi(argv[1]);
    89|    if (size <= 0) size = DATA_SIZE;
    90|
    91|    srand(42);
    92|    struct timespec t0, t1;
    93|
    94|    printf("=== C Performance Demo OPTIMIZED (size=%d) ===\n\n", size);
    95|
    96|    /* --- 1. 数组遍历 (替代链表) --- */
    97|    clock_gettime(CLOCK_MONOTONIC, &t0);
    98|    ItemOpt *items = malloc(size * sizeof(ItemOpt));
    99|    for (int i = 0; i < size; i++) {
   100|        items[i].value = rand() % size;
   101|        snprintf(items[i].name, NAME_LEN, "item_%d", i);
   102|    }
   103|    long long arr_sum = sum_array_opt(items, size);
   104|    clock_gettime(CLOCK_MONOTONIC, &t1);
   105|    double arr_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   106|    printf("[1] Array sum = %lld, time = %.4f s\n\n", arr_sum, arr_time);
   107|
   108|    /* --- 2. qsort (替代冒泡排序) --- */
   109|    int *sort_arr = malloc(size * sizeof(int));
   110|    for (int i = 0; i < size; i++) sort_arr[i] = rand() % size;
   111|
   112|    clock_gettime(CLOCK_MONOTONIC, &t0);
   113|    qsort(sort_arr, size, sizeof(int), cmp_int);
   114|    clock_gettime(CLOCK_MONOTONIC, &t1);
   115|    double sort_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   116|    printf("[2] qsort (%d items): %.4f s\n\n", size, sort_time);
   117|
   118|    /* --- 3. 预分配 (替代循环 malloc) --- */
   119|    clock_gettime(CLOCK_MONOTONIC, &t0);
   120|    StringPool *sp = process_strings_opt(size);
   121|    clock_gettime(CLOCK_MONOTONIC, &t1);
   122|    double malloc_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   123|    printf("[3] Pre-allocated pool (%d strings): %.4f s\n\n", size, malloc_time);
   124|
   125|    /* --- 4. 缓存 strlen --- */
   126|    clock_gettime(CLOCK_MONOTONIC, &t0);
   127|    int long_names = count_long_names_opt(sp);
   128|    clock_gettime(CLOCK_MONOTONIC, &t1);
   129|    double strlen_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   130|    printf("[4] Cached strlen (%d long names): %.4f s\n\n", long_names, strlen_time);
   131|
   132|    /* --- 5. 无泄漏 --- */
   133|    printf("[5] No leak demo:\n");
   134|    no_leak_memory();
   135|    printf("\n");
   136|
   137|    /* --- 汇总 --- */
   138|    double total = arr_time + sort_time + malloc_time + strlen_time;
   139|    printf("=== Total time: %.4f s ===\n", total);
   140|
   141|    /* 清理 */
   142|    free(items);
   143|    free(sort_arr);
   144|    string_pool_free(sp);
   145|
   146|    return 0;
   147|}
   148|