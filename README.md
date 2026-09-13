# Purpose
Once, I had a CTF challenge that involved reverse engineering Python bytecode to break out of a Python jail. There are a few tools that already exist for this, such as the dis and x-python libraries, but I struggled to get them to work.

So, I made pdbug, which functions as a disassembler and debugger for Python bytecode, that decompiles the bytecode as you run it.

# Usage
All you need is the file `pdbug.py`. To load your bytecode program, edit the variables at the top of the file:
```python
######################
#  EDIT THESE FIELDS #
######################
TEST_BYTECODE = bytes.fromhex('')
TEST_VARIABLE_NAMES = []
TEST_CONSTANTS = []
TEST_GLOBAL_FUNCTIONS = []
TEST_NAMES = []
######################
```

An example program is already loaded for your convenience. To run the debugger, just do `python3 pdbug.py` and you will be put in a gdb-like environment. If you're ever unsure about a command, `help` is available.

# TO-DO
Features:
- Support multiple versions of Python (currently only supports Python 3.10.10)
- Implement `DEREF` and `CLOSURE` instructions
- Set up proper error handling
