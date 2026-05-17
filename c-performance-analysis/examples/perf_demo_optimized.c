/*
 * perf_demo_optimized.c — 修复所有性能问题的优化版本
 *
 * 优化对照:
 *   1. 链表 → 数组 (缓存友好)
 *   2. 冒泡排序 O(n²) → qsort O(n log n)
 *   3. 循环中反复 malloc → 预分配大缓冲区
 *   4. 重复 strlen → 缓存长度
 *   5. 内存泄漏 → 修复 free
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define DATA_SIZE 50000
#define NAME_LEN 32
#define BUF_SIZE 256

/* ===== 优化1: 用数组替代链表 (缓存友好) ===== */
typedef struct {
    int value;
    char name[NAME_LEN];
    struct { int next; } link;  /* 用索引替代指针，数据连续 */
} ItemOpt;

long long sum_array_opt(ItemOpt *items, int size) {
    long long total = 0;
    for (int i = 0; i < size; i++) {
        total += items[i].value;
    }
    return total;
}

/* ===== 优化2: qsort O(n log n) 替代冒泡排序 ===== */
int cmp_int(const void *a, const void *b) {
    return *(const int *)a - *(const int *)b;
}

/* ===== 优化3: 预分配缓冲区，避免循环中反复 malloc ===== */
typedef struct {
    char *pool;       /* 大缓冲区 */
    int *offsets;     /* 每个字符串的偏移 */
    int count;
} StringPool;

StringPool *process_strings_opt(int count) {
    StringPool *sp = malloc(sizeof(StringPool));
    sp->count = count;
    sp->pool = malloc(count * BUF_SIZE);    /* 一次性分配 */
    sp->offsets = malloc(count * sizeof(int));
    for (int i = 0; i < count; i++) {
        sp->offsets[i] = i * BUF_SIZE;
        snprintf(sp->pool + sp->offsets[i], BUF_SIZE,
                 "processed_result_%d_with_extra_padding_data", i);
    }
    return sp;
}

void string_pool_free(StringPool *sp) {
    free(sp->pool);
    free(sp->offsets);
    free(sp);
}

/* ===== 优化4: 缓存 strlen 结果 ===== */
int count_long_names_opt(StringPool *sp) {
    int long_count = 0;
    for (int i = 0; i < sp->count; i++) {
        size_t len = strlen(sp->pool + sp->offsets[i]);  /* 只算一次 */
        if (len > 20) long_count++;
    }
    return long_count;
}

/* ===== 优化5: 修复内存泄漏 ===== */
void no_leak_memory(void) {
    char *buf = malloc(1024 * 1024);
    snprintf(buf, 64, "this memory is properly freed");
    printf("  [safe ptr] %s\n", buf);
    free(buf);  /* ✅ 正确释放 */
}

/* ===== 主程序 ===== */
int main(int argc, char *argv[]) {
    int size = DATA_SIZE;
    if (argc > 1) size = atoi(argv[1]);
    if (size <= 0) size = DATA_SIZE;

    srand(42);
    struct timespec t0, t1;

    printf("=== C Performance Demo OPTIMIZED (size=%d) ===\n\n", size);

    /* --- 1. 数组遍历 (替代链表) --- */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    ItemOpt *items = malloc(size * sizeof(ItemOpt));
    for (int i = 0; i < size; i++) {
        items[i].value = rand() % size;
        snprintf(items[i].name, NAME_LEN, "item_%d", i);
    }
    long long arr_sum = sum_array_opt(items, size);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double arr_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[1] Array sum = %lld, time = %.4f s\n\n", arr_sum, arr_time);

    /* --- 2. qsort (替代冒泡排序) --- */
    int *sort_arr = malloc(size * sizeof(int));
    for (int i = 0; i < size; i++) sort_arr[i] = rand() % size;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    qsort(sort_arr, size, sizeof(int), cmp_int);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double sort_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[2] qsort (%d items): %.4f s\n\n", size, sort_time);

    /* --- 3. 预分配 (替代循环 malloc) --- */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    StringPool *sp = process_strings_opt(size);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double malloc_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[3] Pre-allocated pool (%d strings): %.4f s\n\n", size, malloc_time);

    /* --- 4. 缓存 strlen --- */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int long_names = count_long_names_opt(sp);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double strlen_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[4] Cached strlen (%d long names): %.4f s\n\n", long_names, strlen_time);

    /* --- 5. 无泄漏 --- */
    printf("[5] No leak demo:\n");
    no_leak_memory();
    printf("\n");

    /* --- 汇总 --- */
    double total = arr_time + sort_time + malloc_time + strlen_time;
    printf("=== Total time: %.4f s ===\n", total);

    /* 清理 */
    free(items);
    free(sort_arr);
    string_pool_free(sp);

    return 0;
}
