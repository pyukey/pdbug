### REFERENCES ###
# dis: https://docs.python.org/3.5/library/dis.html#python-bytecode-instructions
# code: https://docs.python.org/3/c-api/code.html
# guide: https://www.goldsborough.me/python/low-level/2016/10/04/00-31-30-disassembling_python_bytecode/

ASM_INSTR = {
  0x01: "POP_TOP",
  0x04: "DUP_TOP",
  0x16: "BINARY_MODULO",
  0x17: "BINARY_ADD",
  0x1a: "BINARY_FLOOR_DIVIDE",
  0x37: "INPLACE_ADD",
  0x53: "RETURN_VALUE",
  0x57: "POP_BLOCK",
  0x59: "POP_EXCEPT",
  0x64: "LOAD_CONST",
  0x6b: "COMPARE_OP",
  0x6e: "JUMP_FORWARD",
  0x72: "POP_JUMP_IF_FALSE",
  0x74: "LOAD_GLOBAL",
  0x77: "RERAISE",
  0x79: "JUMP_IF_NOT_EXC_MATCH",
  0x7a: "SETUP_FINALLY",
  0x7c: "LOAD_FAST",
  0x7d: "STORE_FAST",
  0x7e: "DELETE_FAST",
  0x83: "CALL_FUNCTION"
}

def disassemble(bytecode, program)

class Code:
    def __init__(self, bytecode, variables, constants, functions):
        self.variables = variables
        self.contants = constants
        self.globals = functions
        self.stack = []
        self.rsp = 0
        disassemble(bytecode, self.program)
        self.rip = 0

    def pop(self):
        self.rsp -= 1
        return self.stack[self.rsp]

    def push(self, val):
        self.stack[self.rsp] = val
        self.rsp += 1

    
