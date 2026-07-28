#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <locale.h>
#include <wchar.h>

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#include <conio.h>
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#define sleep_ms(ms) Sleep(ms)
#define mkdir_p(path) _mkdir(path)
#else
#include <unistd.h>
#include <termios.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#define sleep_ms(ms) usleep((ms) * 1000)
#define mkdir_p(path) mkdir(path, 0755)
#endif

#define VERSION "1.0.0"

typedef enum {
    DIR_UP = 0,
    DIR_RIGHT = 1,
    DIR_DOWN = 2,
    DIR_LEFT = 3
} Direction;

typedef struct {
    int pipes;
    int fps;
    int steady;
    int limit;
    int random_start;
    int bold;
    int color;
    int keep_style;
    int colors[16];
    int num_colors;
    int pipe_types[16];
    int num_pipe_types;
} PipeConfig;

typedef struct {
    int x;
    int y;
    Direction direction;
    int pipe_type;
    int color;
} Pipe;

// 10 Wide Character Pipe Line Sets (Heavy, Curved, Light, Double, Pure ASCII)
static const wchar_t *PIPE_LINE_SETS_W[10][16] = {
    /* Style 0: Heavy Box Lines */
    {L"┃", L"┏", L" ", L"┓", L"┛", L"━", L"┓", L" ", L" ", L"┗", L"┃", L"┛", L"┗", L" ", L"┏", L"━"},

    /* Style 1: Curved Box Lines */
    {L"│", L"╭", L" ", L"╮", L"╯", L"─", L"╮", L" ", L" ", L"╰", L"│", L"╯", L"╰", L" ", L"╭", L"─"},

    /* Style 2: Light Box Lines */
    {L"│", L"┌", L" ", L"┐", L"┘", L"─", L"┐", L" ", L" ", L"└", L"│", L"┘", L"└", L" ", L"┌", L"─"},

    /* Style 3: Double Box Lines */
    {L"║", L"╔", L" ", L"╗", L"╝", L"═", L"╗", L" ", L" ", L"╚", L"║", L"╝", L"╚", L" ", L"╔", L"═"},

    /* Style 4: Clean Pure ASCII Lines */
    {L"|", L"+", L" ", L"+", L"+", L"-", L"+", L" ", L" ", L"+", L"|", L"+", L"+", L" ", L"+", L"-"},

    /* Style 5: Heavy Lines */
    {L"┃", L"┏", L" ", L"┓", L"┛", L"━", L"┓", L" ", L" ", L"┗", L"┃", L"┛", L"┗", L" ", L"┏", L"━"},

    /* Style 6: Curved Lines */
    {L"│", L"╭", L" ", L"╮", L"╯", L"─", L"╮", L" ", L" ", L"╰", L"│", L"╯", L"╰", L" ", L"╭", L"─"},

    /* Style 7: Light Lines */
    {L"│", L"┌", L" ", L"┐", L"┘", L"─", L"┐", L" ", L" ", L"└", L"│", L"┘", L"└", L" ", L"┌", L"─"},

    /* Style 8: Double Lines */
    {L"║", L"╔", L" ", L"╗", L"╝", L"═", L"╗", L" ", L" ", L"╚", L"║", L"╝", L"╚", L" ", L"╔", L"═"},

    /* Style 9: Heavy Mixed Box Lines */
    {L"╿", L"┍", L" ", L"┑", L"┚", L"╾", L"┑", L" ", L" ", L"┕", L"╽", L"┙", L"┕", L" ", L"┎", L"╾"}
};

static PipeConfig get_default_config(void) {
    PipeConfig cfg;
    cfg.pipes = 1;
    cfg.fps = 75;
    cfg.steady = 13;
    cfg.limit = 2000;
    cfg.random_start = 0;
    cfg.bold = 1;
    cfg.color = 1;
    cfg.keep_style = 0;

    int default_colors[] = {1, 2, 3, 4, 5, 6, 7, 0};
    cfg.num_colors = 8;
    for (int i = 0; i < 8; i++) cfg.colors[i] = default_colors[i];

    cfg.num_pipe_types = 1;
    cfg.pipe_types[0] = 0;
    return cfg;
}

static void get_config_filepath(char *buf, size_t size) {
    const char *home = getenv("USERPROFILE");
    if (!home) home = getenv("HOME");
    if (!home) home = ".";
#if defined(_WIN32) || defined(_WIN64)
    snprintf(buf, size, "%s\\AppData\\Local\\pipes-py\\config.json", home);
#else
    snprintf(buf, size, "%s/.config/pipes-py/config.json", home);
#endif
}

static void load_config(PipeConfig *cfg) {
    *cfg = get_default_config();
    char filepath[512];
    get_config_filepath(filepath, sizeof(filepath));

    FILE *f = fopen(filepath, "r");
    if (!f) return;

    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (strstr(line, "\"pipes\"")) sscanf(line, " %*[^:]: %d", &cfg->pipes);
        else if (strstr(line, "\"fps\"")) sscanf(line, " %*[^:]: %d", &cfg->fps);
        else if (strstr(line, "\"steady\"")) sscanf(line, " %*[^:]: %d", &cfg->steady);
        else if (strstr(line, "\"limit\"")) sscanf(line, " %*[^:]: %d", &cfg->limit);
        else if (strstr(line, "\"random_start\"")) {
            cfg->random_start = strstr(line, "true") != NULL;
        } else if (strstr(line, "\"bold\"")) {
            cfg->bold = strstr(line, "true") != NULL;
        } else if (strstr(line, "\"color\"")) {
            cfg->color = strstr(line, "true") != NULL;
        } else if (strstr(line, "\"keep_style\"")) {
            cfg->keep_style = strstr(line, "true") != NULL;
        }
    }
    fclose(f);
}

static void save_config(const PipeConfig *cfg) {
    char filepath[512];
    get_config_filepath(filepath, sizeof(filepath));

    char dir[512];
    strncpy(dir, filepath, sizeof(dir));
    char *last_slash = strrchr(dir, '/');
    if (!last_slash) last_slash = strrchr(dir, '\\');
    if (last_slash) {
        *last_slash = '\0';
        mkdir_p(dir);
    }

    FILE *f = fopen(filepath, "w");
    if (!f) return;

    fprintf(f, "{\n");
    fprintf(f, "  \"pipes\": %d,\n", cfg->pipes);
    fprintf(f, "  \"fps\": %d,\n", cfg->fps);
    fprintf(f, "  \"steady\": %d,\n", cfg->steady);
    fprintf(f, "  \"limit\": %d,\n", cfg->limit);
    fprintf(f, "  \"random_start\": %s,\n", cfg->random_start ? "true" : "false");
    fprintf(f, "  \"bold\": %s,\n", cfg->bold ? "true" : "false");
    fprintf(f, "  \"color\": %s,\n", cfg->color ? "true" : "false");
    fprintf(f, "  \"keep_style\": %s,\n", cfg->keep_style ? "true" : "false");
    fprintf(f, "  \"colors\": [1, 2, 3, 4, 5, 6, 7, 0],\n");
    fprintf(f, "  \"pipe_types\": [%d]\n", cfg->pipe_types[0]);
    fprintf(f, "}\n");
    fclose(f);
}

// Terminal Control & ANSI Helpers

#if defined(_WIN32) || defined(_WIN64)
static DWORD orig_console_mode = 0;

static void setup_terminal(void) {
    SetConsoleOutputCP(65001);
    SetConsoleCP(65001);

    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut != INVALID_HANDLE_VALUE) {
        GetConsoleMode(hOut, &orig_console_mode);
        DWORD mode = orig_console_mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING;
        SetConsoleMode(hOut, mode);
    }
    _setmode(_fileno(stdout), _O_U16TEXT);

    // Switch to alternate screen, hide cursor, clear screen
    wprintf(L"\x1b[?1049h\x1b[?25l\x1b[2J");
    fflush(stdout);
}

static void restore_terminal(void) {
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut != INVALID_HANDLE_VALUE && orig_console_mode != 0) {
        SetConsoleMode(hOut, orig_console_mode);
    }

    // Show cursor, restore main screen
    wprintf(L"\x1b[0m\x1b[?25h\x1b[?1049l");
    fflush(stdout);
}

static void get_terminal_size(int *width, int *height) {
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (GetConsoleScreenBufferInfo(hOut, &csbi)) {
        *width = csbi.srWindow.Right - csbi.srWindow.Left + 1;
        *height = csbi.srWindow.Bottom - csbi.srWindow.Top + 1;
    } else {
        *width = 80;
        *height = 24;
    }
}

static int get_key_nonblocking(void) {
    if (_kbhit()) {
        return _getch();
    }
    return -1;
}

#else

static struct termios orig_termios;

static void restore_terminal(void) {
    tcsetattr(STDIN_FILENO, TCSANOW, &orig_termios);
    wprintf(L"\x1b[0m\x1b[?25h\x1b[?1049l");
    fflush(stdout);
}

static void setup_terminal(void) {
    tcgetattr(STDIN_FILENO, &orig_termios);
    struct termios raw = orig_termios;
    raw.c_lflag &= ~(ECHO | ICANON);
    tcsetattr(STDIN_FILENO, TCSANOW, &raw);

    int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);

    wprintf(L"\x1b[?1049h\x1b[?25l\x1b[2J");
    fflush(stdout);
    atexit(restore_terminal);
}

static void get_terminal_size(int *width, int *height) {
    struct winsize ws;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_col > 0 && ws.ws_row > 0) {
        *width = ws.ws_col;
        *height = ws.ws_row;
    } else {
        *width = 80;
        *height = 24;
    }
}

static int get_key_nonblocking(void) {
    unsigned char ch;
    if (read(STDIN_FILENO, &ch, 1) == 1) {
        return ch;
    }
    return -1;
}

#endif

static void clear_screen(void) {
    wprintf(L"\x1b[2J\x1b[H");
    fflush(stdout);
}

static void draw_pipe_segment(int y, int x, int pipe_type, Direction old_dir, Direction new_dir, int color, int bold, int use_color) {
    int index = old_dir * 4 + new_dir;
    const wchar_t *ch = (index >= 0 && index < 16) ? PIPE_LINE_SETS_W[pipe_type % 10][index] : L" ";

    // ANSI positioning (1-indexed row, col)
    wprintf(L"\x1b[%d;%dH", y + 1, x + 1);

    if (use_color) {
        int ansi_color = 30 + (color % 8);
        if (color % 8 == 0) ansi_color = 37; // Default/white if 0
        if (bold) {
            wprintf(L"\x1b[1;%dm%ls\x1b[0m", ansi_color, ch);
        } else {
            wprintf(L"\x1b[0;%dm%ls\x1b[0m", ansi_color, ch);
        }
    } else {
        if (bold) {
            wprintf(L"\x1b[1m%ls\x1b[0m", ch);
        } else {
            wprintf(L"\x1b[0m%ls", ch);
        }
    }
}

static void print_usage(const char *prog) {
    printf("Usage: %s [OPTIONS]\n", prog);
    printf("Animated pipes in clean line ASCII / Unicode\n\n");
    printf("Options:\n");
    printf("  -p, --pipes INT        Number of pipes\n");
    printf("  -f, --fps INT          Frames per second (20-100)\n");
    printf("  -s, --steady INT       Steadiness (5-15)\n");
    printf("  -r, --limit INT        Character limit before reset\n");
    printf("  -R, --random           Random start\n");
    printf("  -B, --no-bold          Disable bold\n");
    printf("  -C, --no-color         Disable color\n");
    printf("  -P, --pipe-style INT   Change pipe style (0-9)\n");
    printf("  -K, --keep-style       Keep style on wrap\n");
    printf("  -S, --save-config      Save current settings as default\n");
    printf("  -v, --version          Show version\n");
    printf("  -h, --help             Show this help message\n");
}

int main(int argc, char **argv) {
    setlocale(LC_ALL, "");
    srand((unsigned int)time(NULL));

    PipeConfig config;
    load_config(&config);

    int do_save = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--version") == 0) {
            printf("pipes-c v%s\n", VERSION);
            return 0;
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if ((strcmp(argv[i], "-p") == 0 || strcmp(argv[i], "--pipes") == 0) && i + 1 < argc) {
            config.pipes = atoi(argv[++i]);
            if (config.pipes < 1) config.pipes = 1;
        } else if ((strcmp(argv[i], "-f") == 0 || strcmp(argv[i], "--fps") == 0) && i + 1 < argc) {
            config.fps = atoi(argv[++i]);
            if (config.fps < 20) config.fps = 20;
            if (config.fps > 100) config.fps = 100;
        } else if ((strcmp(argv[i], "-s") == 0 || strcmp(argv[i], "--steady") == 0) && i + 1 < argc) {
            config.steady = atoi(argv[++i]);
            if (config.steady < 5) config.steady = 5;
            if (config.steady > 15) config.steady = 15;
        } else if ((strcmp(argv[i], "-r") == 0 || strcmp(argv[i], "--limit") == 0) && i + 1 < argc) {
            config.limit = atoi(argv[++i]);
            if (config.limit < 0) config.limit = 0;
        } else if (strcmp(argv[i], "-R") == 0 || strcmp(argv[i], "--random") == 0) {
            config.random_start = 1;
        } else if (strcmp(argv[i], "-B") == 0 || strcmp(argv[i], "--no-bold") == 0) {
            config.bold = 0;
        } else if (strcmp(argv[i], "-C") == 0 || strcmp(argv[i], "--no-color") == 0) {
            config.color = 0;
        } else if (strcmp(argv[i], "-K") == 0 || strcmp(argv[i], "--keep-style") == 0) {
            config.keep_style = 1;
        } else if ((strcmp(argv[i], "-P") == 0 || strcmp(argv[i], "--pipe-style") == 0) && i + 1 < argc) {
            int style = atoi(argv[++i]);
            if (style >= 0 && style <= 9) {
                config.pipe_types[0] = style;
                config.num_pipe_types = 1;
            }
        } else if (strcmp(argv[i], "-S") == 0 || strcmp(argv[i], "--save-config") == 0) {
            do_save = 1;
        }
    }

    if (do_save) {
        save_config(&config);
    }

    setup_terminal();

    int height, width;
    get_terminal_size(&width, &height);

    Pipe *pipes = malloc(sizeof(Pipe) * config.pipes);
    for (int i = 0; i < config.pipes; i++) {
        pipes[i].direction = config.random_start ? (Direction)(rand() % 4) : DIR_UP;
        pipes[i].x = config.random_start ? (rand() % width) : (width / 2);
        pipes[i].y = config.random_start ? (rand() % height) : (height / 2);
        pipes[i].pipe_type = config.pipe_types[rand() % config.num_pipe_types];
        pipes[i].color = config.colors[rand() % config.num_colors];
    }

    int count = 0;
    int delay_ms = 1000 / config.fps;
    int running = 1;

    while (running) {
        int ch = get_key_nonblocking();
        if (ch != -1) {
            char key = (ch >= 0 && ch <= 255) ? (char)ch : 0;
            if (key >= 'a' && key <= 'z') key -= 32;

            if (key == 'P' && config.steady < 15) config.steady++;
            else if (key == 'O' && config.steady > 3) config.steady--;
            else if (key == 'F' && config.fps < 100) {
                config.fps++;
                delay_ms = 1000 / config.fps;
            } else if (key == 'D' && config.fps > 20) {
                config.fps--;
                delay_ms = 1000 / config.fps;
            } else if (key == 'B') {
                config.bold = !config.bold;
            } else if (key == 'C') {
                config.color = !config.color;
            } else if (key == 'K') {
                config.keep_style = !config.keep_style;
            } else if (key == '?' || ch == 27) {
                running = 0;
                break;
            }
        }

        int new_w, new_h;
        get_terminal_size(&new_w, &new_h);
        if (new_h != height || new_w != width) {
            height = new_h;
            width = new_w;
            clear_screen();
        }

        for (int i = 0; i < config.pipes; i++) {
            Pipe *p = &pipes[i];
            int x = p->x;
            int y = p->y;
            Direction old_dir = p->direction;

            if (old_dir % 2 != 0) {
                x += -old_dir + 2;
            } else {
                y += old_dir - 1;
            }

            if (x < 0 || x >= width || y < 0 || y >= height) {
                if (!config.keep_style) {
                    p->pipe_type = config.pipe_types[rand() % config.num_pipe_types];
                    p->color = config.colors[rand() % config.num_colors];
                }
                x = (x % width + width) % width;
                y = (y % height + height) % height;
            }

            Direction new_dir = old_dir;
            if (rand() % config.steady <= 1) {
                int turn = 2 * (rand() % 2) - 1;
                new_dir = (Direction)((old_dir + turn + 4) % 4);
            }

            draw_pipe_segment(p->y, p->x, p->pipe_type, old_dir, new_dir, p->color, config.bold, config.color);

            p->x = x;
            p->y = y;
            p->direction = new_dir;
        }

        fflush(stdout);

        count += config.pipes;
        if (config.limit > 0 && count >= config.limit) {
            clear_screen();
            count = 0;
        }

        sleep_ms(delay_ms);
    }

    free(pipes);
    restore_terminal();
    return 0;
}
