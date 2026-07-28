#include <stdio.h>

int add(int left, int right)
{
    return left + right;
}

int main()
{
    int total = add(20, 22);
    printf("picoc Python demo: %d\n", total);
    return 0;
}
