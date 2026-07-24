### REFERENCES ###
# dis: https://docs.python.org/3.5/library/dis.html#python-bytecode-instructions
# code: https://docs.python.org/3/c-api/code.html
# guide: https://www.goldsborough.me/python/low-level/2016/10/04/00-31-30-disassembling_python_bytecode/

STACK_SIZE = 0x100
CALL_STACK_SIZE = 0X10

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

def disassemble(bytecode, offset):
    if len(bytecode) % 2 != 0:
        raise ValueError("Bytecode length must be even")

    instructions = [None for _ in range(offset)]
    for i in range(0, len(bytecode), 2):
        instructions.append((bytecode[i], bytecode[i + 1]))

    return instructions

class Code:
    def __init__(self, bytecode, variables, constants, functions):
        self.offset = 30
        self.variables = variables
        self.constants = constants
        self.globals = functions
        self.stack = [None] * STACK_SIZE
        self.rsp = 0
        self.program = disassemble(bytecode, self.offset)
        self.rip = self.offset
        self.breakpoints = []

    def pop(self):
        self.rsp -= 1
        return self.stack[self.rsp]

    def push(self, val):
        self.stack[self.rsp] = val
        self.rsp += 1

    def POP_TOP(self, val):
        self.pop()

    def DUP_TOP(self, val):
        tos = self.pop()
        self.push(tos)
        self.push(tos)

    def BINARY_MODULO(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 % tos)
    
    def BINARY_FLOOR_DIVIDE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 // tos)
        
    def INPLACE_ADD(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 + tos)

    def RETURN_VALUE(self, val):
        raise RuntimeError("RETURN_VALUE has not been implemented") # TODO: properly implement return with a call stack. For now, it's handled in cont

    def POP_BLOCK(self, val):
        raise RuntimeError("POP_BLOCK has not been implemented") # TODO: figure out how to handle blocks

    def POP_EXCEPT(self, val):
        raise RuntimeError("POP_EXCEPT has not been implemented") # TODO: figure out how to handle blocks

    def LOAD_CONST(self, val):
        self.push(self.constants[val])

    def COMPARE_OP(self, val):
        tos = self.pop()
        tos1 = self.pop()
        match val:
            case 0: push(tos1 < tos)
            case 1: push(tos1 <= tos)
            case 2: push(tos1 == tos)
            case 3: push(tos1 != tos)
            case 4: push(tos1 > tos)
            case 5: push(tos1 >= tos)

    def JUMP_FORWARD(self, val):
        self.rip += val

    def POP_JUMP_IF_FALSE(self, val):
        tos = self.pop()
        if tos == False:
            self.rip = val - 1

    def LOAD_GLOBAL(self, val):
        self.push(self.globals[val])

    def JUMP_IF_NOT_EXEC_MATCH(self, val):
        raise RuntimeError("JUMP_IF_NOT_EXEC_MATCH is not implemented") # TODO: figure out what this does

    def SETUP_FINALLY(self, val):
        self.rip += val # TODO: Figure out what this does

    def LOAD_FAST(self, val):
        self.push(self.variables[val])

    def STORE_FAST(self, val):
        self.variables[val] = self.pop()

    def DELETE_FAST(self, val):
        del self.variables[val]

    def CALL_FUNCTION(self, val):
        argv = [None for _ in range(val)]
        for i in range(val-1, -1, -1):
            argv[i] = pop()
        func = getattr(builtins, self.pop())

        if func:
            self.push(func(*argv))


    def stepi(self):
        inst = ASM_INSTR[self.program[self.rip][0]]
        param = [self.program[self.rip][1]]
        getattr(self, inst)(*param)
        self.rip += 1

    def cont(self):
        while self.rip < len(self.program) and (self.program[self.rip][0] != 0x53) and (self.rip not in self.breakpoints):
            self.stepi()
        
    def run(self):
        self.rip = self.offset
        self.rsp = 0
        self.cont()

# Test Example
test_code = Code(bytes.fromhex('640004003700'), ['a'], [1,12,123], ['max'])
test_code.run()
print(test_code.pop())
