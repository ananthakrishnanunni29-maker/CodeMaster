CC ?= gcc
CFLAGS ?= -O2 -Wall -std=c99

TARGET = pipes

all: $(TARGET)

$(TARGET): pipes.c
	$(CC) $(CFLAGS) pipes.c -o $(TARGET)

clean:
	rm -f $(TARGET) $(TARGET).exe

.PHONY: all clean
