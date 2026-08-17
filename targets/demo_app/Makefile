CC ?= clang
CFLAGS ?= -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined
TARGET = demo_vuln
SRC = demo_vuln.c

.PHONY: all build clean test fuzz

all: build

build:
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

# Standalone fuzz harness entry — reads stdin, feeds parse_message
fuzz: build
	@echo "Deterministic fuzz via Python discovery engine (see ../../scripts/demo.sh)"
	@python3 -c "from discovery.fuzzing_adapter import fuzz_binary; import json; print(json.dumps(fuzz_binary('./$(TARGET)'), indent=2))"

test: build
	@bash tests/regression.sh ./$(TARGET)

clean:
	rm -f $(TARGET)
