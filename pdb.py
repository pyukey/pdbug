### REFERENCES ###
# dis: https://docs.python.org/3.5/library/dis.html#python-bytecode-instructions
# code: https://docs.python.org/3/c-api/code.html
# guide: https://www.goldsborough.me/python/low-level/2016/10/04/00-31-30-disassembling_python_bytecode/

STACK_SIZE = 0x100
CALL_STACK_SIZE = 0x10
BLOCK_STACK_SIZE = 0x10

BLOCK_TYPES = ["try", "except", "finally"]

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

def disassemble(bytecode):
    if len(bytecode) % 2 != 0:
        raise ValueError("Bytecode length must be even")

    instructions = []
    for i in range(0, len(bytecode), 2):
        instructions.append((bytecode[i], bytecode[i + 1]))

    return instructions

class Code:
    class Block:
        def __init__(block_type, return_addr):
            if block_type not in BLOCK_TYPES:
                raise ValueError(blocktype, "is not a recognized block type.")
            self.type = block_type
            self.addr = return_addr
            
    def __init__(self, bytecode, variables, constants, functions):
        self.variables = variables
        self.constants = constants
        self.globals = functions
        self.stack = [None] * STACK_SIZE
        self.rsp = 0
        self.bstack = [None] * BLOCK_STACK_SIZE
        self.rbp = 0
        self.program = disassemble(bytecode)
        self.rip = 0
        self.breakpoints = []

    def pop(self):
        self.rsp -= 1
        return self.stack[self.rsp]

    def push(self, val):
        self.stack[self.rsp] = val
        self.rsp += 1

    def bpop(self):
        self.rbp -= 1
        return self.bstack[self.rbp]

    def bpush(self, val):
        self.bstack[self.rbp] = val
        self.rbp += 1

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
        self.bpop()

    def POP_EXCEPT(self, val):
        raise RuntimeError("An Exception", self.pop(), "has occurred") # TODO: figure out how to handle blocks

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
        tos = self.pop()
        if type(tos) is Exception:
            self.rip = val - 1 

    def SETUP_FINALLY(self, val):
        self.bpush
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
        if self.rip >= len(self.program):
            print("ERROR: Instruction", self.rip, "is outside the scope of the program")
            return -1
        inst = ASM_INSTR[self.program[self.rip][0]]
        param = [self.program[self.rip][1]]
        getattr(self, inst)(*param)
        self.rip += 1

    def cont(self):
        while self.rip < len(self.program):
            if self.program[self.rip][0] == 0x53:
                print("Program ended with return value", val)
                return self.pop()
            self.stepi()
            if self.rip in self.breakpoints:
                print("Breakpoint hit at instruction", self.rip)
                return None
        if self.rip == len(self.program):
            print("ERROR: end of program reached without return value")
        else:
            print("ERROR: instruction", self.rip, "is outside the scope of the program")

    def reset(self, command):
        self.rip = 0
        self.rsp = 0
        self.rbp = 0
        for i in range(1,len(command)):
            self.variables[i-1] = eval(command[i])

    def run(self, command):
        self.reset(command)
        val = self.cont()

    def tui(self):
        while True:
            command = input("> ").split(' ')
            match command[0]:
                case 'b' | 'break':
                    self.breakpoints.append(int(command[1]))
                case 'r' | 'run':
                    self.run(command)
                case 'c' | 'continue':
                    self.cont()
                case 'si' | 'step-instruction':
                    self.stepi()
                case 'starti':
                    self.reset(command)
                case 's' | 'set':
                    if len(command) > 1:
                        match command[1]:
                            case 'rip':
                                self.rip = int(command[2])
                            case 'rsp':
                                self.rsp = int(command[2])
                            case 'rbp':
                                self.rbp = int(command[2])
                            case 'stack':
                                idx = int(command[2])
                                self.stack[idx] = eval(command[3])
                            case 'var':
                                idx = int(command[2])
                                self.variables[idx] = eval(command[3])
                            case 'const':
                                idx = int(command[2])
                                self.constants[idx] = eval(command[3])
                            case 'global':
                                idx = int(command[2])
                                self.globals[idx] = eval(command[3])
                            case 'h' | 'help':
                                print(self.rbp)
                            case _:
                                print(self.rbp)
                case 'p' | 'print':
                    if len(command) > 1:
                        match command[1]:
                            case 'rip':
                                print(self.rip)
                            case 'rsp':
                                print(self.rsp)
                            case 'rbp':
                                print(self.rbp)
                            case 'stack':
                                if len(command) == 2:
                                    for i in range(self.rsp-1, -1, -1):
                                        print(i,":", self.stack[i])
                                else:
                                    idx = int(command[2])
                                    print(idx,":", self.stack[idx])
                            case 'program':
                                if len(command) == 2:
                                    for i in range(len(self.program)-1, -1, -1):
                                        preface = " *" if i == self.rip else "  "
                                        print(preface,i,":", ASM_INSTR[self.program[i][0]], "(", self.program[i][1], ")")
                                else:
                                    idx = int(command[2])
                                    print(idx,":", ASM_INSTR[self.program[idx][0]], "(", self.program[idx][1], ")")
                            case 'var':
                                if len(command) == 2:
                                    print(self.variables)
                                else:
                                    print(self.variables[int(command[2])])
                            case 'const':
                                if len(command) == 2:
                                    print(self.constants)
                                else:
                                    print(self.constants[int(command[2])])
                            case 'global':
                                if len(command) == 2:
                                    print(self.globals)
                                else:
                                    print(self.globals[int(command[2])])
                            case 'h' | 'help':
                                print(self.rbp)
                            case _:
                                print(eval(command[1]))
                    
                case 'h' | 'help':
                    print('idk buster, figure it out yourself')
                case 'e' | 'exit':
                    return 0
                case _:
                    print('Command', command[0], 'is not a recognized command')
# Test Example
test_code = Code(bytes.fromhex('640004003700'), ['a', 'b', 'c', 'd'], [1,12,123], ['max'])
test_code.tui()
