CC ?= clang
CFLAGS ?= -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined

TARGET=targets/demo_app/demo_vuln
VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: all demo build clean test venv report dashboard benchmark

all: demo

venv:
	python3 -m venv $(VENV)
	$(PIP) install -q -r requirements.txt

build:
	$(CC) $(CFLAGS) targets/demo_app/demo_vuln.c -o $(TARGET)

demo: venv build
	bash scripts/demo.sh

test: venv build
	$(PY) -m pytest tests/ -v

report:
	$(PY) verification/report.py

benchmark: venv build
	$(PY) scripts/demo.py --benchmark

dashboard-export: venv
	$(PY) scripts/demo.py --export-dashboard

clean:
	rm -f $(TARGET)
	rm -rf reports/*/ reports/run.json reports/run.md reports/latest.json
	rm -rf runtime/ebpf/*.bpf.o
