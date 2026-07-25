### REFERENCES ###
# dis: https://docs.python.org/3.5/library/dis.html#python-bytecode-instructions
# code: https://docs.python.org/3/c-api/code.html
# guide: https://www.goldsborough.me/python/low-level/2016/10/04/00-31-30-disassembling_python_bytecode/

import builtins

STACK_SIZE = 0x100
CALL_STACK_SIZE = 0x10
BLOCK_STACK_SIZE = 0x10

ERROR_TYPES = ["return", "known-error", "unknown"]


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
    class CodeError(Exception):
        def __init__(self, error_type, message):
            if error_type not in ERROR_TYPES:
                raise ValueError(error_type, "is not a recognized CodeError type.")
            self.type = error_type
            self.message = message

    class Block:
        def __init__(self, return_addr):
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

    # Typically used in preparation of Error-handling, since restoring the exception state requires multiple values to be popped
    def DUP_TOP(self, val):
        tos = self.pop()
        self.push(tos)
        self.push(tos)

    def BINARY_MODULO(self, val):
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 % tos)
        except:
            raise self.CodeError('known-error', 'Attempted to do modulo by a non-negative number')
    
    def BINARY_FLOOR_DIVIDE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 // tos)
        except:
            raise self.CodeError('known-error', 'Division by 0 occurred.')
        
    def INPLACE_ADD(self, val):
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 + tos)
        except:
            raise self.CodeError('known-error', "Values "+str(tos1)+" and "+str(tos)+" cannot be added together")

    def RETURN_VALUE(self, val):
        raise self.CodeError('return', val)

    def POP_BLOCK(self, val):
        self.bpop()

    def POP_EXCEPT(self, val):
        raise Coderror('known-error', self.pop())

    def LOAD_CONST(self, val):
        self.push(self.constants[val])

    def COMPARE_OP(self, val):
        tos = self.pop()
        tos1 = self.pop()
        match val:
            case 0: self.push(tos1 < tos)
            case 1: self.push(tos1 <= tos)
            case 2: self.push(tos1 == tos)
            case 3: self.push(tos1 != tos)
            case 4: self.push(tos1 > tos)
            case 5: self.push(tos1 >= tos)

    def JUMP_FORWARD(self, val):
        self.rip += val

    def POP_JUMP_IF_FALSE(self, val):
        tos = self.pop()
        if tos == False:
            self.rip = val - 1

    def LOAD_GLOBAL(self, val):
        self.push(self.globals[val])

    def JUMP_IF_NOT_EXC_MATCH(self, val):
        tos = self.pop()
        if type(tos) is Exception:
            self.rip = val - 1 

    def SETUP_FINALLY(self, val):
        self.bpush(self.Block(val+self.rip))

    def LOAD_FAST(self, val):
        self.push(self.variables[val])

    def STORE_FAST(self, val):
        self.variables[val] = self.pop()

    def DELETE_FAST(self, val):
        del self.variables[val]

    def CALL_FUNCTION(self, val):
        argv = [None for _ in range(val)]
        for i in range(val-1, -1, -1):
            argv[i] = self.pop()
        func = getattr(builtins, self.pop())

        try:
            if func:
                self.push(func(*argv))
        except:
            raise self.CodeError('known-error', "The called function "+func+" encountered an exception.")

    def stepi(self):
        if self.rip >= len(self.program):
            raise self.CodeError('unkown', "Instruction" +str(self.rip)+ "is outside the scope of the program.")
            
        inst = ASM_INSTR[self.program[self.rip][0]]
        param = [self.program[self.rip][1]]
        getattr(self, inst)(*param)
        self.rip += 1

    def cont(self, steps):
        while self.rip < len(self.program):
            try:
                self.stepi()
            except self.CodeError as e:
                match e.type:
                    case 'return':
                        print("Program returned value:", e.message)
                        return
                    case 'known-error':
                        print("Program hit an exception:", e.message)
                        block = self.bpop()
                        self.rip = block.addr+1
                    case 'unknown':
                        print("Unexpected error raised:", e.message)
                    case _:
                        raise RuntimeError("Unknown CodeError encountered: \nType: " + e.type + "\nMessage: " + e.message)
            except Exception as e:
                raise e
                 
            if self.rip in self.breakpoints:
                print("Breakpoint hit at instruction", self.rip)
                return

            steps -= 1
            if steps == 0:
                return

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
        self.cont(-1)

    def tui(self):
        while True:
            command = input("> ").split(' ')
            match command[0]:
                case 'b' | 'break':
                    self.breakpoints.append(int(command[1]))
                case 'r' | 'run':
                    self.run(command)
                case 'c' | 'continue':
                    self.cont(-1)
                case 'si' | 'step-instruction':
                    self.cont(1)
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
test_code = Code(bytes.fromhex('64017c0037007d00740064027c0064031a0083027d027a067c007c0216007d0257006e1e04007401792f01007d0301007a127c0164046b0272245700590064007d037e03640553005700590064007d037e036406530064007d037e03770177007c0064076b05724d7c00740274037c0183018301160064026b02724b740474057c01830174036b0272487c01830153006408830153006406530074037c01830174067c00830117005300'), ['', '', '', ''], [None,83,0,97,'cat','/','',123,'0'], ['max','Exception','len','str','eval','type','chr'])
test_code.tui()
