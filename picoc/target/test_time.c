#include <stdio.h>
#include <time.h>

int main() {
    time_t t;
    time(&t);
    printf("time: %d\n", (int)t);
    return 0;
}
