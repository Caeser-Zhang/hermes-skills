/*
 * perf_demo.c — 故意包含多种性能问题的示例程序
 *
 * 问题清单:
 *   1. 循环中反复 malloc/free (堆分配开销)
 *   2. 链表遍历 (缓存不友好)
 *   3. O(n²) 算法 (低效排序)
 *   4. 内存泄漏 (忘记 free)
 *   5. 过度使用 strlen (重复计算)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define DATA_SIZE 50000
#define NAME_LEN 32

/* ===== 问题1: 链表 — 缓存不友好 ===== */
typedef struct Node {
    int value;
    char name[NAME_LEN];
    struct Node *next;
} Node;

Node *create_node(int val, const char *name) {
    Node *n = malloc(sizeof(Node));
    if (!n) return NULL;
    n->value = val;
    strncpy(n->name, name, NAME_LEN - 1);
    n->name[NAME_LEN - 1] = '\0';
    n->next = NULL;
    return n;
}

Node *build_linked_list(int size) {
    Node head = {0, "", NULL};
    Node *tail = &head;
    for (int i = 0; i < size; i++) {
        char name[NAME_LEN];
        snprintf(name, NAME_LEN, "item_%d", i);
        tail->next = create_node(rand() % size, name);
        tail = tail->next;
    }
    return head.next;
}

/* 链表遍历求和 — 缓存不友好 (指针追逐) */
long long sum_linked_list(Node *head) {
    long long total = 0;
    while (head) {
        total += head->value;
        head = head->next;
    }
    return total;
}

void free_linked_list(Node *head) {
    while (head) {
        Node *tmp = head;
        head = head->next;
        free(tmp);
    }
}

/* ===== 问题2: 数组 — 缓存友好 (对比用) ===== */
typedef struct {
    int value;
    char name[NAME_LEN];
} Item;

long long sum_array(Item *items, int size) {
    long long total = 0;
    for (int i = 0; i < size; i++) {
        total += items[i].value;
    }
    return total;
}

/* ===== 问题3: O(n²) 冒泡排序 ===== */
void bubble_sort(int *arr, int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int tmp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = tmp;
            }
        }
    }
}

/* ===== 问题4: 循环中反复 malloc/free ===== */
char **process_strings(int count) {
    char **results = malloc(count * sizeof(char *));
    for (int i = 0; i < count; i++) {
        /* 每次循环都分配和释放 — 应该预分配复用 */
        char *buf = malloc(256);
        snprintf(buf, 256, "processed_result_%d_with_extra_padding_data", i);
        results[i] = buf;
    }
    return results;
}

/* ===== 问题5: 重复调用 strlen ===== */
int count_long_names(char **strings, int count) {
    int long_count = 0;
    for (int i = 0; i < count; i++) {
        /* 每次循环都调用 strlen — 编译器不一定能优化 */
        if (strlen(strings[i]) > 20) {
            long_count++;
        }
        if (strlen(strings[i]) > 10) {  /* 又算一遍 */
            /* do nothing, just waste cycles */
        }
    }
    return long_count;
}

/* ===== 问题6: 内存泄漏 ===== */
void leak_memory(void) {
    /* 故意泄漏: 忘记 free */
    char *leaked = malloc(1024 * 1024);  /* 1MB 泄漏 */
    snprintf(leaked, 64, "this memory is leaked");
    printf("  [leaked ptr] %s\n", leaked);
    /* 没有 free(leaked) ! */
}

/* ===== 主程序 ===== */
int main(int argc, char *argv[]) {
    int size = DATA_SIZE;
    if (argc > 1) size = atoi(argv[1]);
    if (size <= 0) size = DATA_SIZE;

    srand(42);
    struct timespec t0, t1;

    printf("=== C Performance Demo (size=%d) ===\n\n", size);

    /* --- 1. 链表遍历 vs 数组遍历 --- */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    Node *list = build_linked_list(size);
    long long list_sum = sum_linked_list(list);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double list_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[1] Linked list sum = %lld, time = %.4f s\n", list_sum, list_time);

    clock_gettime(CLOCK_MONOTONIC, &t0);
    Item *items = malloc(size * sizeof(Item));
    for (int i = 0; i < size; i++) {
        items[i].value = rand() % size;
    }
    long long arr_sum = sum_array(items, size);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double arr_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[1] Array     sum = %lld, time = %.4f s  (%.1fx faster)\n\n",
           arr_sum, arr_time, list_time / arr_time);

    /* --- 2. 冒泡排序 --- */
    int *sort_arr = malloc(size * sizeof(int));
    for (int i = 0; i < size; i++) sort_arr[i] = rand() % size;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    bubble_sort(sort_arr, size);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double sort_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[2] Bubble sort (%d items): %.4f s\n\n", size, sort_time);

    /* --- 3. 循环中反复 malloc --- */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    char **strings = process_strings(size);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double malloc_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[3] Repeated malloc (%d strings): %.4f s\n\n", size, malloc_time);

    /* --- 4. 重复 strlen --- */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    int long_names = count_long_names(strings, size);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double strlen_time = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("[4] Repeated strlen (%d long names): %.4f s\n\n", long_names, strlen_time);

    /* --- 5. 内存泄漏 --- */
    printf("[5] Memory leak demo:\n");
    leak_memory();
    printf("\n");

    /* --- 汇总 --- */
    double total = list_time + arr_time + sort_time + malloc_time + strlen_time;
    printf("=== Total time: %.4f s ===\n", total);

    /* 清理（但 leak_memory 的泄漏故意不清理） */
    free_linked_list(list);
    free(items);
    free(sort_arr);
    for (int i = 0; i < size; i++) free(strings[i]);
    free(strings);

    return 0;
}
