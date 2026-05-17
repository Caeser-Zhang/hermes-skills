     1|/*
     2| * perf_demo.c — 故意包含多种性能问题的示例程序
     3| *
     4| * 问题清单:
     5| *   1. 循环中反复 malloc/free (堆分配开销)
     6| *   2. 链表遍历 (缓存不友好)
     7| *   3. O(n²) 算法 (低效排序)
     8| *   4. 内存泄漏 (忘记 free)
     9| *   5. 过度使用 strlen (重复计算)
    10| */
    11|
    12|#include <stdio.h>
    13|#include <stdlib.h>
    14|#include <string.h>
    15|#include <time.h>
    16|
    17|#define DATA_SIZE 50000
    18|#define NAME_LEN 32
    19|
    20|/* ===== 问题1: 链表 — 缓存不友好 ===== */
    21|typedef struct Node {
    22|    int value;
    23|    char name[NAME_LEN];
    24|    struct Node *next;
    25|} Node;
    26|
    27|Node *create_node(int val, const char *name) {
    28|    Node *n = malloc(sizeof(Node));
    29|    if (!n) return NULL;
    30|    n->value = val;
    31|    strncpy(n->name, name, NAME_LEN - 1);
    32|    n->name[NAME_LEN - 1] = '\0';
    33|    n->next = NULL;
    34|    return n;
    35|}
    36|
    37|Node *build_linked_list(int size) {
    38|    Node head = {0, "", NULL};
    39|    Node *tail = &head;
    40|    for (int i = 0; i < size; i++) {
    41|        char name[NAME_LEN];
    42|        snprintf(name, NAME_LEN, "item_%d", i);
    43|        tail->next = create_node(rand() % size, name);
    44|        tail = tail->next;
    45|    }
    46|    return head.next;
    47|}
    48|
    49|/* 链表遍历求和 — 缓存不友好 (指针追逐) */
    50|long long sum_linked_list(Node *head) {
    51|    long long total = 0;
    52|    while (head) {
    53|        total += head->value;
    54|        head = head->next;
    55|    }
    56|    return total;
    57|}
    58|
    59|void free_linked_list(Node *head) {
    60|    while (head) {
    61|        Node *tmp = head;
    62|        head = head->next;
    63|        free(tmp);
    64|    }
    65|}
    66|
    67|/* ===== 问题2: 数组 — 缓存友好 (对比用) ===== */
    68|typedef struct {
    69|    int value;
    70|    char name[NAME_LEN];
    71|} Item;
    72|
    73|long long sum_array(Item *items, int size) {
    74|    long long total = 0;
    75|    for (int i = 0; i < size; i++) {
    76|        total += items[i].value;
    77|    }
    78|    return total;
    79|}
    80|
    81|/* ===== 问题3: O(n²) 冒泡排序 ===== */
    82|void bubble_sort(int *arr, int n) {
    83|    for (int i = 0; i < n - 1; i++) {
    84|        for (int j = 0; j < n - i - 1; j++) {
    85|            if (arr[j] > arr[j + 1]) {
    86|                int tmp = arr[j];
    87|                arr[j] = arr[j + 1];
    88|                arr[j + 1] = tmp;
    89|            }
    90|        }
    91|    }
    92|}
    93|
    94|/* ===== 问题4: 循环中反复 malloc/free ===== */
    95|char **process_strings(int count) {
    96|    char **results = malloc(count * sizeof(char *));
    97|    for (int i = 0; i < count; i++) {
    98|        /* 每次循环都分配和释放 — 应该预分配复用 */
    99|        char *buf = malloc(256);
   100|        snprintf(buf, 256, "processed_result_%d_with_extra_padding_data", i);
   101|        results[i] = buf;
   102|    }
   103|    return results;
   104|}
   105|
   106|/* ===== 问题5: 重复调用 strlen ===== */
   107|int count_long_names(char **strings, int count) {
   108|    int long_count = 0;
   109|    for (int i = 0; i < count; i++) {
   110|        /* 每次循环都调用 strlen — 编译器不一定能优化 */
   111|        if (strlen(strings[i]) > 20) {
   112|            long_count++;
   113|        }
   114|        if (strlen(strings[i]) > 10) {  /* 又算一遍 */
   115|            /* do nothing, just waste cycles */
   116|        }
   117|    }
   118|    return long_count;
   119|}
   120|
   121|/* ===== 问题6: 内存泄漏 ===== */
   122|void leak_memory(void) {
   123|    /* 故意泄漏: 忘记 free */
   124|    char *leaked = malloc(1024 * 1024);  /* 1MB 泄漏 */
   125|    snprintf(leaked, 64, "this memory is leaked");
   126|    printf("  [leaked ptr] %s\n", leaked);
   127|    /* 没有 free(leaked) ! */
   128|}
   129|
   130|/* ===== 主程序 ===== */
   131|int main(int argc, char *argv[]) {
   132|    int size = DATA_SIZE;
   133|    if (argc > 1) size = atoi(argv[1]);
   134|    if (size <= 0) size = DATA_SIZE;
   135|
   136|    srand(42);
   137|    struct timespec t0, t1;
   138|
   139|    printf("=== C Performance Demo (size=%d) ===\n\n", size);
   140|
   141|    /* --- 1. 链表遍历 vs 数组遍历 --- */
   142|    clock_gettime(CLOCK_MONOTONIC, &t0);
   143|    Node *list = build_linked_list(size);
   144|    long long list_sum = sum_linked_list(list);
   145|    clock_gettime(CLOCK_MONOTONIC, &t1);
   146|    double list_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   147|    printf("[1] Linked list sum = %lld, time = %.4f s\n", list_sum, list_time);
   148|
   149|    clock_gettime(CLOCK_MONOTONIC, &t0);
   150|    Item *items = malloc(size * sizeof(Item));
   151|    for (int i = 0; i < size; i++) {
   152|        items[i].value = rand() % size;
   153|    }
   154|    long long arr_sum = sum_array(items, size);
   155|    clock_gettime(CLOCK_MONOTONIC, &t1);
   156|    double arr_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   157|    printf("[1] Array     sum = %lld, time = %.4f s  (%.1fx faster)\n\n",
   158|           arr_sum, arr_time, list_time / arr_time);
   159|
   160|    /* --- 2. 冒泡排序 --- */
   161|    int *sort_arr = malloc(size * sizeof(int));
   162|    for (int i = 0; i < size; i++) sort_arr[i] = rand() % size;
   163|
   164|    clock_gettime(CLOCK_MONOTONIC, &t0);
   165|    bubble_sort(sort_arr, size);
   166|    clock_gettime(CLOCK_MONOTONIC, &t1);
   167|    double sort_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   168|    printf("[2] Bubble sort (%d items): %.4f s\n\n", size, sort_time);
   169|
   170|    /* --- 3. 循环中反复 malloc --- */
   171|    clock_gettime(CLOCK_MONOTONIC, &t0);
   172|    char **strings = process_strings(size);
   173|    clock_gettime(CLOCK_MONOTONIC, &t1);
   174|    double malloc_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   175|    printf("[3] Repeated malloc (%d strings): %.4f s\n\n", size, malloc_time);
   176|
   177|    /* --- 4. 重复 strlen --- */
   178|    clock_gettime(CLOCK_MONOTONIC, &t0);
   179|    int long_names = count_long_names(strings, size);
   180|    clock_gettime(CLOCK_MONOTONIC, &t1);
   181|    double strlen_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
   182|    printf("[4] Repeated strlen (%d long names): %.4f s\n\n", long_names, strlen_time);
   183|
   184|    /* --- 5. 内存泄漏 --- */
   185|    printf("[5] Memory leak demo:\n");
   186|    leak_memory();
   187|    printf("\n");
   188|
   189|    /* --- 汇总 --- */
   190|    double total = list_time + arr_time + sort_time + malloc_time + strlen_time;
   191|    printf("=== Total time: %.4f s ===\n", total);
   192|
   193|    /* 清理（但 leak_memory 的泄漏故意不清理） */
   194|    free_linked_list(list);
   195|    free(items);
   196|    free(sort_arr);
   197|    for (int i = 0; i < size; i++) free(strings[i]);
   198|    free(strings);
   199|
   200|    return 0;
   201|}
   202|