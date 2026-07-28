#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <wchar.h>
#include <locale.h>

static const wchar_t *MATRIX_CHARS[] = {
    L"- ", L"* ", L"% ", L"& ", L"# ", L"@ ", L"1 ", L"2 ", L"3 ", L"4 ",
    L"5 ", L"6 ", L"7 ", L"8 ", L"9 ", L"0 ",
    L"\u30A2", L"\u30A3", L"\u30A4", L"\u30A5", L"\u30A6", L"\u30A7",
    L"\u30A8", L"\u30A9", L"\u30AA",
    L"\u30AB", L"\u30AC", L"\u30AD", L"\u30AE", L"\u30AF", L"\u30B0",
    L"\u30B1", L"\u30B2", L"\u30B3",
    L"\u30B4", L"\u30B5", L"\u30B6", L"\u30B7", L"\u30B8", L"\u30B9",
    L"\u30BA", L"\u30BB", L"\u30BC", L"\u30BD", L"\u30BE",
    L"\u30BF", L"\u30C0", L"\u30C1", L"\u30C2", L"\u30C3", L"\u30C4",
    L"\u30C5", L"\u30C6"
};
static const int MATRIX_CHARS_COUNT = sizeof(MATRIX_CHARS) / sizeof(MATRIX_CHARS[0]);

static const char *TERMINAL_COLOURS[] = {"22", "28"};
static const int TERMINAL_COLOURS_COUNT = 2;

typedef struct {
    int screen_width;
    int line_count;
    double line_speed;
    int *line_array;
} Matrix;

void Matrix_init(Matrix *m, int screen_width, int line_count, double line_speed) {
    m->screen_width = screen_width;
    m->line_count = line_count;
    m->line_speed = line_speed;
    m->line_array = (int *)malloc(screen_width * sizeof(int));
}

void Matrix_setScreenLineArray(Matrix *m) {
    for (int i = 0; i < m->screen_width; i++) {
        m->line_array[i] = 1;
    }
}

const char *Matrix_getTextColourLightGreenChar(void) {
    return "\033[38;5;15m";
}

const char *Matrix_getTextColourRandomChar(void) {
    int randomIndex = rand() % TERMINAL_COLOURS_COUNT;
    static char buf[32];
    snprintf(buf, sizeof(buf), "\033[38;5;%sm", TERMINAL_COLOURS[randomIndex]);
    return buf;
}

const wchar_t *Matrix_getCharacter(void) {
    int randomIndex = rand() % MATRIX_CHARS_COUNT;
    return MATRIX_CHARS[randomIndex];
}

void Matrix_startMatrix(Matrix *m) {
    Matrix_setScreenLineArray(m);
    for (int l = 0; l < m->line_count; l++) {
        for (int col = 0; col < m->screen_width; col++) {
            int n = m->line_array[col];
            if (n == 1 || n == 2) {
                if (n == 2) {
                    printf("%s%ls", Matrix_getTextColourLightGreenChar(), Matrix_getCharacter());
                    m->line_array[col] = 1;
                } else {
                    printf("%s%ls", Matrix_getTextColourRandomChar(), Matrix_getCharacter());
                }
                if (1 == (rand() % 30 + 1)) {
                    m->line_array[col] = 0;
                }
            } else {
                printf("%s ", Matrix_getTextColourRandomChar());
                if (1 == (rand() % 60 + 1)) {
                    m->line_array[col] = 2;
                }
            }
        }
        printf("\n");
        struct timespec ts;
        ts.tv_sec = (time_t)m->line_speed;
        ts.tv_nsec = (long)((m->line_speed - (double)ts.tv_sec) * 1000000000.0);
        nanosleep(&ts, NULL);
    }
}

void Matrix_destroy(Matrix *m) {
    free(m->line_array);
}

int main(void) {
    setlocale(LC_ALL, "");
    srand((unsigned int)time(NULL));
    Matrix matrix;
    Matrix_init(&matrix, 150, 750, 0.1);
    Matrix_startMatrix(&matrix);
    Matrix_destroy(&matrix);
    return 0;
}