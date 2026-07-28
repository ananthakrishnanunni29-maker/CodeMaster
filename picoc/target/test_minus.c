#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int add(int a, int b) {
    return a + b;
}

int main() {
    printf("add(-1, 1) = %d\n", add(-1, 1));
    return 0;
}
