### REFERENCES ###
# dis: https://docs.python.org/3.10/library/dis.html#python-bytecode-instructions
# code: https://docs.python.org/3/c-api/code.html
# guide: https://www.goldsborough.me/python/low-level/2016/10/04/00-31-30-disassembling_python_bytecode/

import builtins
import shlex
import types
from collections import abc
import inspect
import asyncio

STACK_SIZE = 0x100
CALL_STACK_SIZE = 0x10
BLOCK_STACK_SIZE = 0x10

ERROR_TYPES = ["return", "known-error", "unknown"]


ASM_INSTR = {
  0x01: "POP_TOP",
  0x02: "ROT_TWO",
  0x03: "ROT_THREE",
  0x04: "DUP_TOP",
  0x05: "DUP_TOP_TWO",
  0x06: "ROT_FOUR",
  0x09: "NOP",
  0x0a: "UNARY_POSITIVE",
  0x0b: "UNARY_NEGATIVE",
  0x0c: "UNARY_NOT",
  0x0f: "UNARY_INVERT",
  0x10: "BINARY_MATRIX_MULTIPLY",
  0x11: "INPLACE_MATRIX_MULTIPLY",
  0x13: "BINARY_POWER",
  0x14: "BINARY_MULTIPLY",
  0x16: "BINARY_MODULO",
  0x17: "BINARY_ADD",
  0x18: "BINARY_SUBTRACT",
  0x19: "BINARY_SUBSCR",
  0x1a: "BINARY_FLOOR_DIVIDE",
  0x1b: "BINARY_TRUE_DIVIDE",
  0x1c: "INPLACE_FLOOR_DIVIDE",
  0x1d: "INPLACE_TRUE_DIVIDE",
  0x1e: "GET_LEN",
  0x1f: "MATCH_MAPPING",
  0x20: "MATCH_SEQUENCE",
  0x21: "MATCH_KEYS",
  0x22: "COPY_DICT_WITHOUT_KEYS",
  0x31: "WITH_EXCEPT_START",
  0x32: "GET_AITER",
  0x33: "GET_ANEXT",
  0x34: "BEFORE_ASYNC_WITH",
  0x36: "END_ASYNC_FOR",
  0x37: "INPLACE_ADD",
  0x38: "INPLACE_SUBTRACT",
  0x39: "INPLACE_MULTIPLY",
  0x3b: "INPLACE_MODULO",
  0x3c: "STORE_SUBSCR",
  0x3d: "DELETE_SUBSCR",
  0x3e: "BINARY_LSHIFT",
  0x3f: "BINARY_RSHIFT",
  0x40: "BINARY_AND",
  0x41: "BINARY_XOR",
  0x42: "BINARY_OR",
  0x43: "INPLACE_POWER",
  0x44: "GET_ITER",
  0x45: "GET_YIELD_FROM_ITER",
  0x46: "PRINT_EXPR",
  0x47: "LOAD_BUILD_CLASS",
  0x48: "YIELD_FROM",
  0x49: "GET_AWAITABLE",
  0x4a: "LOAD_ASSERTION_ERROR",
  0x4b: "INPLACE_LSHIFT",
  0x4c: "INPLACE_RSHIFT",
  0x4d: "INPLACE_AND",
  0x4e: "INPLACE_XOR",
  0x4f: "INPLACE_OR",
  0x52: "LIST_TO_TUPLE",
  0x53: "RETURN_VALUE",
  0x54: "IMPORT_STAR",
  0x55: "SETUP_ANNOTATIONS",
  0x56: "YIELD_VALUE",
  0x57: "POP_BLOCK",
  0x59: "POP_EXCEPT",
  0x5a: "STORE_NAME",
  0x5b: "DELETE_NAME",
  0x5c: "UNPACK_SEQUENCE",
  0x5d: "FOR_ITER",
  0x5e: "UNPACK_EX",
  0x5f: "STORE_ATTR",
  0x60: "DELETE_ATTR",
  0x61: "STORE_GLOBAL",
  0x62: "DELETE_GLOBAL",
  0x63: "ROT_N",
  0x64: "LOAD_CONST",
  0x65: "LOAD_NAME",
  0x66: "BUILD_TUPLE",
  0x67: "BUILD_LIST",
  0x68: "BUILD_SET",
  0x69: "BUILD_MAP",
  0x6a: "LOAD_ATTR",
  0x6b: "COMPARE_OP",
  0x6c: "IMPORT_NAME",
  0x6d: "IMPORT_FROM",
  0x6e: "JUMP_FORWARD",
  0x6f: "JUMP_IF_FALSE_OR_POP",
  0x70: "JUMP_IF_TRUE_OR_POP",
  0x71: "JUMP_ABSOLUTE",
  0x72: "POP_JUMP_IF_FALSE",
  0x73: "POP_JUMP_IF_TRUE",
  0x74: "LOAD_GLOBAL",
  0x75: "IS_OP",
  0x76: "CONTAINS_OP",
  0x77: "RERAISE",
  0x79: "JUMP_IF_NOT_EXC_MATCH",
  0x7a: "SETUP_FINALLY",
  0x7c: "LOAD_FAST",
  0x7d: "STORE_FAST",
  0x7e: "DELETE_FAST",
  0x81: "GEN_START",
  0x82: "RAISE_VARARGS",
  0x83: "CALL_FUNCTION",
  0x84: "MAKE_FUNCTION",
  0x85: "BUILD_SLICE",
  0x87: "LOAD_CLOSURE",
  0x88: "LOAD_DEREF",
  0x89: "STORE_DEREF",
  0x8a: "DELETE_DEREF",
  0x8d: "CALL_FUNCTION_KW",
  0x8e: "CALL_FUNCTION_EX",
  0x8f: "SETUP_WITH",
  0x90: "EXTENDED_ARG",
  0x91: "LIST_APPEND",
  0x92: "SET_ADD",
  0x93: "MAP_ADD",
  0x94: "LOAD_CLASSDEREF",
  0x98: "MATCH_CLASS",
  0x9a: "SETUP_ASYNC_WITH",
  0x9b: "FORMAT_VALUE",
  0x9c: "BUILD_CONST_KEY_MAP",
  0x9d: "BUILD_STRING",
  0xa0: "LOAD_METHOD",
  0xa1: "CALL_METHOD",
  0xa2: "LIST_EXTEND",
  0xa3: "SET_UPDATE",
  0xa4: "DICT_MERGE",
  0xa5: "DICT_UPDATE"
}

ASM_STR = {
  0x01: "",
  0x02: "tos1, tos = tos, tos1",
  0x03: "tos2, tos1, tos = tos, tos2, tos1",
  0x04: "",
  0x05: "",
  0x06: "tos3, tos2, tos1, tos = tos, tos3, tos2, tos1",
  0x09: "",
  0x0a: "+tos",
  0x0b: "-tos",
  0x0c: "not tos",
  0x0f: "~tos",
  0x10: "tos1 * tos",
  0x11: "tos1 *= tos",
  0x13: "tos1 ** tos",
  0x14: "tos1 * tos",
  0x16: "tos1 % tos",
  0x17: "tos1 + tos",
  0x18: "tos1 - tos",
  0x19: "tos1[tos]",
  0x1a: "tos1 // tos",
  0x1b: "tos1 / tos",
  0x1c: "tos1 //= tos",
  0x1d: "tos1 /= tos",
  0x1e: "len(tos)",
  0x1f: "tos isinstance abc.Mapping",
  0x20: "tos isinstance abc.Sequence",
  0x21: "tos1[tos]",
  0x22: "{k:v for k,v in tos1.items() if k not in tos}",
  0x31: "",
  0x32: "tos.__aiter__()",
  0x33: "tos.__anext__()",
  0x34: "",
  0x36: "",
  0x37: "tos1 += tos",
  0x38: "tos1 -= tos",
  0x39: "tos1 *= tos",
  0x3b: "tos1 %= tos",
  0x3c: "tos1[tos] = tos2",
  0x3d: "del tos1[tos]",
  0x3e: "tos1 << tos",
  0x3f: "tos1 >> tos",
  0x40: "tos1 & tos",
  0x41: "tos1 ^ tos",
  0x42: "tos1 | tos",
  0x43: "tos1 **= tos",
  0x44: "iter(tos)",
  0x45: "iter(tos)",
  0x46: "tos",
  0x47: "builtins.__build_class__()",
  0x48: "yield from tos",
  0x49: "get_awaitable(tos)",
  0x4a: "AssertionError",
  0x4b: "tos1 <<= tos",
  0x4c: "tos1 >>= tos",
  0x4d: "tos1 &= tos",
  0x4e: "tos1 ^= tos",
  0x4f: "tos1 |= tos",
  0x52: "tuple(tos)",
  0x53: "return tos",
  0x54: "from tos import *",
  0x55: "",
  0x56: "yield tos",
  0x57: "",
  0x59: "",
  0x5a: "names[i] = tos",
  0x5b: "del names[i]",
  0x5c: "",
  0x5d: "for v in tos",
  0x5e: "",
  0x5f: "tos.names[i] = tos1",
  0x60: "del tos.names[i]",
  0x61: "globals[i] = tos",
  0x62: "del globals[i]",
  0x63: "tosi, ..., tos2, tos1, tos = tos, tosi, ..., tos2, tos1",
  0x64: "constants[i]",
  0x65: "names[i]",
  0x66: "(tosi, ..., tos1, tos)",
  0x67: "[tosi, ..., tos1, tos]",
  0x68: "{tosi, ..., tos1, tos}",
  0x69: "{tos2i: tos2i1, ..., tos3: tos2, tos1: tos}",
  0x6a: "tos.names[i]",
  0x6b: "tos1 op[i] tos",
  0x6c: "from tos import names[i] (level tos1)",
  0x6d: "from tos import names[i]",
  0x6e: "# go to line +i",
  0x6f: "if tos == False:  # go to line i",
  0x70: "if tos == True:  # go to line i",
  0x71: "# go to line i",
  0x72: "if tos == False:  # go to line i",
  0x73: "if tos == True:  # go to line i",
  0x74: "globals[i]",
  0x75: "tos1 is (not) tos",
  0x76: "tos1 (not) in tos",
  0x77: "raise",
  0x79: "except tos as tos1:  # else go to line i",
  0x7a: "finally: # go to line i",
  0x7c: "var[i]",
  0x7d: "var[i] = tos",
  0x7e: "del var[i]",
  0x81: "next(tos)",
  0x82: "raise tos1 from tos",
  0x83: "tosi(tosi1,...,tos2,tos1,tos)",
  0x84: "types.FunctionType(tos1, tos)",
  0x85: "slice(tos2,tos1,tos)",
  0x87: "",
  0x88: "",
  0x89: "",
  0x8a: "",
  0x8d: "tosi(tosi1,...,tos2,tos1,tos)",
  0x8e: "tosi(tosi1,...,tos2,tos1,tos)",
  0x8f: "",
  0x90: "",
  0x91: "tos1.append(tos)",
  0x92: "tos1.add(tos)",
  0x93: "tos1.add(tos)",
  0x94: "",
  0x98: "isinstance(tos2,tos1)",
  0x9a: "",
  0x9b: "str(tos)",
  0x9c: "{tos: tos1}",
  0x9d: "tosi+...+tos2+tos1+tos",
  0xa0: "tos.names[i]",
  0xa1: "tos1.tos2(tosi)",
  0xa2: "tos1.extend(tos)",
  0xa3: "tos1.update(tos)",
  0xa4: "tos1.merge(tos)",
  0xa5: "tos1.update(tos)"
}

def disassemble(bytecode):
    if len(bytecode) % 2 != 0:
        raise ValueError("Bytecode length must be even")

    instructions = []
    for i in range(0, len(bytecode), 2):
        instructions.append((bytecode[i], bytecode[i + 1]))

    return instructions

def parse_input(text):
    def try_int(s):
        try:
            return int(s)
        except ValueError:
            return s

    return [try_int(item) for item in shlex.split(text)]

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
            
    def __init__(self, bytecode, variables, constants, functions, names):
        self.og_variables = variables
        self.variables = []
        self.og_constants = constants
        self.constants = []
        self.og_globals = functions
        self.globals = []
        self.og_names = names
        self.names = []
        self.stack = [None] * STACK_SIZE
        self.rsp = 0
        self.bstack = [None] * BLOCK_STACK_SIZE
        self.rbp = 0
        self.pstack = [None] * STACK_SIZE
        self.rpp = 0
        self.og_program = disassemble(bytecode)
        self.program = []
        self.pretty_program = ['' for _ in self.og_program] # [ASM_STR[i[0]] for i in self.og_program]
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

    def ppop(self):
        self.rpp -= 1
        return self.pstack[self.rpp]

    def ppush(self, val):
        self.pstack[self.rpp] = val
        self.rpp += 1

    def pretty_print(self, string):
        for _ in range(self.rbp):
            string = '    ' + string
        self.pretty_program[self.rip] = string

    def POP_TOP(self, val):
        # Functionality
        self.pop()

        # Decompilation
        self.ppop()
        self.pretty_program[self.rip] = ''

    def ROT_TWO(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos)
        self.ppush(tos1)
        self.pretty_print('')

    def ROT_THREE(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        tos2 = self.pop()
        self.push(tos)
        self.push(tos2)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        tos2 = self.ppop()
        self.ppush(tos)
        self.ppush(tos2)
        self.ppush(tos1)
        self.pretty_print('')

    def ROT_FOUR(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        tos2 = self.pop()
        tos3 = self.pop()
        self.push(tos)
        self.push(tos3)
        self.push(tos2)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        tos2 = self.ppop()
        tos3 = self.ppop()
        self.ppush(tos)
        self.ppush(tos3)
        self.ppush(tos2)
        self.ppush(tos1)
        self.pretty_print('')

    def ROT_N(self, val):
        # Functionality
        tos = [self.pop() for _ in range(val)]
        self.push(tos[0])
        for i in range(val-1, 0, -1):
            self.push(tos[i])

        # Decompilation
        tos = [self.ppop() for _ in range(val)]
        self.ppush(tos[0])
        for i in range(val-1, 0, -1):
            self.ppush(tos[i])
        self.pretty_print('')

    def NOP(self, val):
        # Functionality

        # Decompilation
        self.pretty_print('')

    def EXTENDED_ARG(self, val):
        # Functionality
        if self.rip >= len(self.program)-1:
            raise Self.CodeError('known-error', 'EXTENDED_ARG is the last instruction')
        combined = val << 8 | self.program[self.rip+1][1]
        self.program[self.rip+1][1] = combined

        # Decompilation
        self.pretty_print('')

    # Typically used in preparation of Error-handling, since restoring the exception state requires multiple values to be popped
    def DUP_TOP(self, val):
        # Functionality
        tos = self.pop()
        self.push(tos)
        self.push(tos)

        # Decompilation
        tos = self.ppop()
        self.ppush(tos)
        self.ppush(tos)
        self.pretty_print('')

    def DUP_TOP_TWO(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1)
        self.push(tos)
        self.push(tos1)
        self.push(tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.ppush(tos)
        self.ppush(tos1)
        self.ppush(tos)
        self.pretty_print('')

    def UNARY_POSITIVE(self, val):
        # Functionality
        tos = self.pop()
        self.push(+tos)

        # Decompilation
        tos = self.ppop()
        self.ppush(f"+{tos}")
        self.pretty_print('')

    def UNARY_NEGATIVE(self, val):
        # Functionality
        tos = self.pop()
        self.push(-tos)

        # Decompilation
        tos = self.ppop()
        self.ppush(f"-{tos}")
        self.pretty_print('')

    def UNARY_NOT(self, val):
        # Functionality
        tos = self.pop()
        self.push(not tos)

        # Decompilation
        tos = self.ppop()
        self.ppush(f"not {tos}")
        self.pretty_print('')

    def UNARY_INVERT(self, val):
        # Functionality
        tos = self.pop()
        self.push(~tos)

        # Decompilation
        tos = self.ppop()
        self.ppush(f"~{tos}")
        self.pretty_print('')

    def BINARY_MATRIX_MULTIPLY(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 @ tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"@= {tos1}")
        else:
            self.ppush(f"{tos1} @ {tos}")
        self.pretty_print('')

    def INPLACE_MATRIX_MULTIPLY(self, val):
        self.BINARY_MATRIX_MULTIPLY(val, True)

    def BINARY_POWER(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 ** tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"**= {tos1}")
        else:
            self.ppush(f"{tos1} ** {tos}")
        self.pretty_print('')

    def INPLACE_POWER(self, val):
        self.BINARY_POWER(val, True)

    def BINARY_MULTIPLY(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 * tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"*= {tos1}")
        else:
            self.ppush(f"{tos1} * {tos}")
        self.pretty_print('')

    def INPLACE_MULTIPLY(self, val):
        self.BINARY_MULTIPLY(val, True)

    def BINARY_MODULO(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 % tos)
        except:
            self.push(self.rip)
            self.push(None)
            self.push(Exception)
            raise self.CodeError('known-error', 'Attempted to do modulo by a non-negative number')

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"%= {tos1}")
        else:
            self.ppush(f"{tos1} % {tos}")
        self.pretty_print('')

    def INPLACE_MODULO(self, val):
        self.BINARY_MODULO(val, True)
    
    def BINARY_ADD(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 + tos)
        except:
            self.push(None)
            raise self.CodeError('known-error', "Values "+str(tos1)+" and "+str(tos)+" cannot be added together")

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"+= {tos1}")
        else:
            self.ppush(f"{tos1} + {tos}")
        self.pretty_print('')

    def INPLACE_ADD(self, val):
        self.BINARY_ADD(val, True)

    def BINARY_SUBTRACT(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 - tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"-= {tos1}")
        else:
            self.ppush(f"{tos1} - {tos}")
        self.pretty_print('')

    def INPLACE_SUBTRACT(self, val):
        self.BINARY_SUBTRACT(val, True)

    def BINARY_SUBSCR(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1[tos])

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(f"{tos1}[{tos}]")
        self.pretty_print('')

    def STORE_SUBSCR(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        tos2 = self.pop()
        tos1[tos] = tos2
        # TODO: Figure out how tos1 is preserved

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if 'INPLACE' in ASM_INSTR[self.program[self.rip-1][0]]:
            self.pretty_print(f"{tos1}[{tos}] {tos2}")
        else:
            self.pretty_print(f"{tos1}[{tos}] = {tos2}")

    def DELETE_SUBSCR(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        del tos1[tos]
        # TODO: Figure out how tos1 is preserved

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.pretty_print(f"del {tos1}[{tos}]")

    def BINARY_FLOOR_DIVIDE(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 // tos)
        except:
            self.push(None)
            raise self.CodeError('known-error', 'Division by 0 occurred.')

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"//= {tos1}")
        else:
            self.ppush(f"{tos1} // {tos}")
        self.pretty_print('')
        
    def INPLACE_FLOOR_DIVIDE(self, val):
        self.BINARY_FLOOR_DIVIDE(val, True)

    def BINARY_TRUE_DIVIDE(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 / tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"/= {tos1}")
        else:
            self.ppush(f"{tos1} / {tos}")
        self.pretty_print('')

    def INPLACE_TRUE_DIVIDE(self, val):
        self.BINARY_TRUE_DIVIDE(val, True)

    def BINARY_LSHIFT(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 << tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"<<= {tos1}")
        else:
            self.ppush(f"{tos1} << {tos}")
        self.pretty_print('')
        

    def INPLACE_LSHIFT(self, val):
        self.BINARY_LSHIFT(val, True)

    def BINARY_RSHIFT(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 >> tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f">>= {tos1}")
        else:
            self.ppush(f"{tos1} >> {tos}")
        self.pretty_print('')

    def INPLACE_RSHIFT(self, val):
        self.BINARY_RSHIFT(val, True)

    def BINARY_AND(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 & tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"&= {tos1}")
        else:
            self.ppush(f"{tos1} & {tos}")
        self.pretty_print('')

    def INPLACE_AND(self, val):
        self.BINARY_AND(val, True)

    def BINARY_XOR(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 ^ tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"^= {tos1}")
        else:
            self.ppush(f"{tos1} ^ {tos}")
        self.pretty_print('')

    def INPLACE_XOR(self, val):
        self.BINARY_XOR(val, True)

    def BINARY_OR(self, val, inplace=False):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 | tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if inplace:
            self.ppush(f"|= {tos1}")
        else:
            self.ppush(f"{tos1} | {tos}")
        self.pretty_print('')

    def INPLACE_OR(self, val):
        self.BINARY_OR(val, True)

    def GET_LEN(self, val):
        # Functionality
        tos = self.pop()
        self.push(len(tos))

        # Decompilation
        tos = self.ppop()
        self.ppush(f"len({tos})")
        self.pretty_print('')

    def MATCH_MAPPING(self, val):
        # Functionality
        tos = self.pop()
        self.push(isinstance(tos, abc.Mapping))

        # Decompilation
        tos = self.pop()
        self.ppush(f"{tos} isinstance abc.Mapping")
        self.pretty_print('')

    def MATCH_SEQUENCE(self, val):
        # Functionality
        tos = self.pop()
        self.push(isinstance(tos, abc.Sequence))

        # Decompilation
        tos = self.pop()
        self.ppush(f"{tos} isinstance abc.Sequence")
        self.pretty_print('')

    def MATCH_KEYS(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        lookups = ()
        for item in tos:
            if item not in tos1:
                self.push(None)
                return
            lookups += (tos1[item],)
        self.push(lookups)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(f"{tos1}[{tos}]")
        self.pretty_print('')

    def MATCH_CLASS(self, val):
        # Functionality
        kw_attrs = self.pop()
        match_class = self.pop()
        subject = self.pop()

        if isinstance(subject, match_class):
            try:
                extracted = tuple(getattr(subject, str(i)) for i in range(val))
                for attr in kw_attrs:
                    extracted += (getattr(subject, attr),)
                self.push(extracted)
                self.push(True)
                return
            except AttributeError:
                pass
        self.push(False)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        tos2 = self.ppop()
        self.ppush(f"{tos2} isinstance {tos1}")
        self.pretty_print('')

    def COPY_DICT_WITHOUT_KEYS(self, val):
        # Functionality
        keys = self.pop()
        old_dict = self.pop()
        new_dict = {k: v for k, v in old_dict.items() if k not in keys}
        self.push(new_dict) 

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(f"\{k:v for k,v in {tos1}.items() if k not in {tos}\}")
        self.pretty_print('')

    def SETUP_WITH(self, val):
        # Functionality
        self.push(getattr(self, '__exit__'))
        self.bpush(self.Block(val))
        result = self.__enter__()
        self.push(result)

        # Decompilation
        self.ppush('__exit__')
        selff.ppush('__enter__()')
        self.pretty_print('')

    # Handles an exception in a with statement
    def WITH_EXCEPT_START(self, val):
        self.CALL_FUNCTION(3, 'with ')

    # TODO: figure out what to do with the value from the generator
    async def GEN_START(self, val):
        # Functionality
        tos = self.pop()
        match val:
            case 0: next(tos)
            case 1: await tos
            case 2: await anext(tos)

        # Decompilation
        tos = self.ppop()
        match val:
            case 0: self.pretty_print(f"next({tos})")
            case 1: self.pretty_print(f"await {tos}")
            case 2: self.pretty_print(f"await anext({tos})")

    def LIST_TO_TUPLE(self, val):
        # Functionality
        tos = self.pop()
        self.push(tuple(tos))

        # Decompilation
        tos = self.ppop()
        self.ppush(f"tuple({tos})")
        self.pretty_print('')

    def BUILD_TUPLE(self, val):
        # Functionality
        self.push(reversed(tuple(self.pop() for _ in range(val))))

        # Decompilation
        tos = reversed([self.ppop() for _ in range(val)])
        self.ppush(f"({', '.join(tos)})")
        self.pretty_print('')

    def BUILD_LIST(self, val):
        # Functionality
        self.push(reversed([self.pop() for _ in range(val)]))

        # Decompilation
        tos = reversed([self.ppop() for _ in range(val)])
        self.ppush(f"[{', '.join(tos)}]")
        self.pretty_print('')

    def BUILD_SET(self, val):
        # Functionality
        self.push({self.pop() for _ in range(val)})

        # Decompilation
        tos = reversed([self.ppop() for _ in range(val)])
        self.ppush(f"{{{', '.join(tos)}}}")
        self.pretty_print('')

    def BUILD_MAP(self, val):
        # Functionality
        pairs = []
        for _ in range(val):
            v = self.pop()
            k = self.pop()
            pairs.append((k,v))
        self.push(dict(reversed(pairs)))

        # Decompilation
        str_pairs = []
        for _ in range(val):
            v = self.ppop()
            k = self.ppop()
            str_pairs.append(f"{k}:{v}")
        self.ppush(f"{{{', '.join(str_pairs)}}}")
        self.pretty_print('')

    def BUILD_CONST_KEY_MAP(self, val):
        # Functionality
        keys = self.pop()
        values = [self.pop() for _ in range(val)]
        values.reverse()
        self.push({keys[i]:values[i] for i in range(val)})

        # Decompilation
        keys = self.ppop()
        values = reversed([self.ppop() for _ in range(val)])
        vals = [f"{keys[i]}:{values[i]}" for i in range(val)]
        self.ppush(f"{{{', '.join(vals)}}}")
        self.pretty_print('')

    def BUILD_STRING(self, val):
        # Functionality
        vals = reversed([self.pop() for _ in range(val)])
        self.push(''.join(vals))

        # Decompilation
        vals = reversed([self.ppop() for _ in range(val)])
        self.ppush(''.join(vals))
        self.pretty_print('')

    def RETURN_VALUE(self, val):
        # Decompilation
        self.pretty_print(f"return {self.ppop()}")

        # Functionality
        raise self.CodeError('return', self.pop())

    def RERAISE(self, val):
        # Decompilation
        self.pretty_print(f"raise {self.ppop()}")

        # Functionality
        raise self.CodeError('known-error', self.pop())

    def RAISE_VARARGS(self, val):
        # Decompilation
        match val:
            case 0: self.pretty_print('raise')
            case 1:
                tos = self.ppop()
                self.pretty_print(f"raise {tos}")
            case 2:
                tos = self.ppop()
                tos1 = self.ppop()
                self.pretty_print(f"raise {tos1} from {tos}")

        # Functionality
        match val:
            case 0: raise # Make sure it is reraising the previous exception
            case 1: 
                tos = self.pop()
                raise tos
            case 2:
                tos = self.pop()
                tos1 = self.pop()
                raise tos1 from tos

    def YIELD_VALUE(self, val):
        # Decompilation
        self.pretty_print(f"yield {self.ppop()}")

        # Functionality
        tos = self.pop()
        yield tos

    # from tos import *
    def IMPORT_STAR(self, val):
        # Functionality
        tos = self.pop()
        names = getattr(tos, '__all__', tos.__dict__.keys())
        for name in names:
            self.current_namespace[name] = getattr(tos, name)

        # Decompilation
        tos = self.ppop()
        self.pretty_print(f"from {tos} import *")

    def IMPORT_NAME(self, val):
        # Functionality
        fromlist = self.pop()
        level = self.pop()
        name = self.names[val]
        module = __import__(name, globals=self.globals, locals=self.locals, fromlist=fromlist, level=level)
        self.push(module)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(f"import {name}")
        self.pretty_print('')

    # Typically followed by STORE_FAST
    def IMPORT_FROM(self, val):
        # Functionality
        module = self.pop()
        name = self.names[val]
        v = getattr(module, name)
        self.push(v)

        # Decompilation
        module = self.ppop()
        self.ppush(f"from {module} import {name}")
        self.pretty_print('')

    def SETUP_ANNOTATIONS(self, val):
        # Functionality
        if '__annotations__' not in self.locals():
            self.locals['__annotations__'] = {}

        # Decompilation
        self.pretty_print('')

    def GET_AITER(self, val):
        # Functionality
        tos = self.pop()
        self.push(tos.__aiter__())

        # Decompilation
        tos = self.ppop()
        self.ppush(f"{tos}.__aiter__()")
        self.pretty_print('')

    def GET_ANEXT(self, val):
        # Decompilation
        tos = self.ppop()
        self.ppush(f"{tos}.__anext__()")

        # Functionality
        tos = self.pop()
        self.push(tos.__anext__())
        self.GET_AWAITABLE(val)

    def GET_AWAITABLE(self, val):
        # Functionality
        tos = self.pop()
        self.push(get_awaitable(tos))

        # Decompilation
        tos = self.ppop()
        self.ppush(f"{tos}.__anext__()")
        self.pretty_print('')

    def GET_ITER(self, val):
        # Functionality
        tos = self.pop()
        self.push(iter(tos))

        # Decompilation
        tos = self.ppop()
        self.ppush(f"iter({tos})")
        self.pretty_print('')

    def GET_YIELD_FROM_ITER(self, val):
        # Functionality
        tos = self.pop()
        if inspect.isgenerator(tos) or inspect.iscoroutine(tos):
            self.push(tos)
        else:
            self.push(iter(tos))

        # Decompilation
        ptos = self.ppop()
        if inspect.isgenerator(tos) or inspect.iscoroutine(tos):
            self.ppush(ptos)
        else:
            self.ppush(f"iter({ptos})")
        self.pretty_print('')

    def FOR_ITER(self, val):
        # Functionality
        tos = self.pop()
        ptos = self.ppop()
        try:
            v = tos.__next__()
            self.push(tos)
            self.push(v)

            # Decompilation
            self.ppush(ptos)
            self.ppush(f"v{self.rbp}")
        except:
            self.rip += val
        
        self.pretty_print(f"for v{self.rbp} in {ptos}:")

    def LIST_APPEND(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        list.append(tos1[-val],tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.append({tos})")

    def LIST_EXTEND(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        list.extend(tos1[-val],tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.extend({tos})")

    def SET_ADD(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        set.add(tos1[-val],tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.add({tos})")

    def SET_UPDATE(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        set.update(tos1[-val],tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.update({tos})")

    def DICT_MERGE(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        duplicates = tos1[-val].keys() & tos.keys()
        if duplicates:
            raise CodeError('known-error', "Duplicate keys " + duplicates + " were found during DICT_MERGE")
        dict.update(tos1[-val],tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.update({tos})")

    def DICT_UPDATE(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        dict.update(tos1[-val],tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.update({tos})")

    def MAP_ADD(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        dict.__setitem__(tos1[-val],tos1,tos)
        self.push(tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.ppush(tos1)
        self.pretty_print(f"{tos1}.add({tos})")

    def BEFORE_ASYNC_WITH(self, val):
        # Functionality
        tos = self.pop()
        self.push(tos.__aexit__)
        self.push(tos.__aenter__())

        # Decompilation
        tos = self.ppop()
        self.ppush(f"{tos}.__aexit__")
        self.ppush(f"{tos}.__aenter__()")
        self.pretty_print('')

    # TODO: Figure out frames
    def SETUP_ASYNC_WITH(self, val):
        raise CodeError('unknown', 'SETUP_ASYNC_WITH has not been implemented yet')

    # Terminates an async for loop
    def END_ASYNC_FOR(self, val):
        tos = self.pop()
        #if tos == StopAsyncIteration:
        #    TODO: Pop 7 values and use the last 3 to handle the exception state
        #else
        #    TODO: Pop 3 values to reraise the exception state
        self.bpop()

    def POP_BLOCK(self, val):
        self.bpop()

    def POP_EXCEPT(self, val):
        self.bpop()

    def IS_OP(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        if val == 1:
            self.push(tos1 is not tos)
        else:
            self.push(tos1 is tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if val == 1:
            self.ppush(f"{tos1} is not {tos}")
        else:
            self.ppush(f"{tos1} is {tos}")
        self.pretty_print('')

    def CONTAINS_OP(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        if val == 1:
            self.push(tos1 not in tos)
        else:
            self.push(tos1 in tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if val == 1:
            self.ppush(f"{tos1} not in {tos}")
        else:
            self.ppush(f"{tos1} in {tos}")
        self.pretty_print('')

    def COMPARE_OP(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        match val:
            case 0: self.push(tos1 < tos)
            case 1: self.push(tos1 <= tos)
            case 2: self.push(tos1 == tos)
            case 3: self.push(tos1 != tos)
            case 4: self.push(tos1 > tos)
            case 5: self.push(tos1 >= tos)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        match val:
            case 0: self.ppush(f"{tos1} < {tos}")
            case 1: self.ppush(f"{tos1} <= {tos}")
            case 2: self.ppush(f"{tos1} == {tos}")
            case 3: self.ppush(f"{tos1} != {tos}")
            case 4: self.ppush(f"{tos1} > {tos}")
            case 5: self.ppush(f"{tos1} >= {tos}")
        self.pretty_print('')

    def JUMP_FORWARD(self, val):
        # Decompilation
        self.pretty_print(f"# go to line {self.rip + val + 1}")

        # Functionality
        self.rip += val

    def JUMP_ABSOLUTE(self, val):
        # Decompilation
        self.pretty_print(f"# go to line {val}")

        # Functionality
        self.rip = val - 1

    def JUMP_IF_FALSE_OR_POP(self, val):
        # Decompilation
        tos = self.ppop()
        self.pretty_print(f"if ! {tos}:  # go to line {val}")
        self.ppush(tos)

        # Functionality
        tos = self.pop()
        if tos == False:
            self.rip = val - 1
            self.push(tos)

    def JUMP_IF_TRUE_OR_POP(self, val):
        # Decompilation
        tos = self.ppop()
        self.pretty_print(f"if {tos}:  # go to line {val}")
        self.ppush(tos)

        # Functionality
        tos = self.pop()
        if tos == True:
            self.rip = val - 1
            self.push(tos)

    def POP_JUMP_IF_FALSE(self, val):
        # Decompilation
        tos = self.ppop()
        self.pretty_print(f"if ! {tos}:  # go to line {val}")

        # Functionality
        tos = self.pop()
        if tos == False:
            self.rip = val - 1

    def POP_JUMP_IF_TRUE(self, val):
        # Decompilation
        tos = self.ppop()
        self.pretty_print(f"if {tos}:  # go to line {val}")

        # Functionality
        tos = self.pop()
        if tos == True:
            self.rip = val - 1

    def JUMP_IF_NOT_EXC_MATCH(self, val):
        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        self.pretty_print(f"except {tos}:  # go to line {val}")

        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        if type(tos1) is type(tos):
            self.rip = val - 1 

    def SETUP_FINALLY(self, val):
        # Decompilation
        self.pretty_print(f"try:  # go to line {val+self.rip+1} if there is an exception")

        # Functionality
        self.bpush(self.Block(val+self.rip))

    def LOAD_CONST(self, val):
        # Functionality
        self.push(self.constants[val])

        # Decompilation
        self.ppush(str(self.constants[val]))
        self.pretty_print('')

    def LOAD_GLOBAL(self, val):
        # Functionality
        self.push(self.globals[val])

        # Decompilation
        self.ppush(str(self.globals[val]))
        self.pretty_print('')

    def STORE_GLOBAL(self, val):
        # Functionality
        self.globals[val] = self.pop()

        # Decompilation
        if 'INPLACE' in ASM_INSTR[self.program[self.rip-1][0]]:
            self.pretty_print(f"globals[{val}] {self.ppop()}")
        else:
            self.pretty_print(f"globals[{val}] = {self.ppop()}")

    def DELETE_GLOBAL(self, val):
        # Functionality
        del self.globals[val]

        # Decompilation
        self.pretty_print(f"del globals[{val}]")

    def LOAD_FAST(self, val):
        # Functionality
        self.push(self.variables[val])

        # Decompilation
        name = self.og_variables[val]
        if name == '':
            self.ppush(f"var{val}")
        else:
            self.ppush(name)
        self.pretty_print('')

    def STORE_FAST(self, val):
        # Functionality
        self.variables[val] = self.pop()

        # Decompilation
        name = self.og_variables[val]
        if name == '':
            name = f"var{val}"
        
        if 'INPLACE' in ASM_INSTR[self.program[self.rip-1][0]]:
            self.pretty_print(f"{name} {self.ppop()}")
        else:
            self.pretty_print(f"{name} = {self.ppop()}")

    def DELETE_FAST(self, val):
        # Functionality
        del self.variables[val]

        # Decompilation
        name = self.og_variables[val]
        if name == '':
            name = f"var{val}"

        self.pretty_print(f"del {name}")

    def LOAD_NAME(self, val):
        # Functionality
        self.push(self.names[val])

        # Decompilation
        self.ppush(str(self.names[val]))
        self.pretty_print('')

    def STORE_NAME(self, val):
        # Functionality
        self.names[val] = self.pop()

        # Decompilation
        if 'INPLACE' in ASM_INSTR[self.program[self.rip-1][0]]:
            self.pretty_print(f"names[{val}] {self.ppop()}")
        else:
            self.pretty_print(f"names[{val}] = {self.ppop()}")

    def DELETE_NAME(self, val):
        # Functionality
        del self.names[val]

        # Decompilation
        self.pretty_print(f"del names[{val}]")

    def LOAD_ATTR(self, val):
        # Functionality
        tos = self.pop()
        self.push(getattr(tos, self.names[val]))

        # Decompilation
        tos = self.ppop()
        self.ppush(f"{tos}.{self.names[val]}")
        self.pretty_print('')

    def STORE_ATTR(self, val):
        # Functionality
        tos = self.pop()
        tos1 = self.pop()
        name = self.names[val]
        setattr(tos, name, tos1)

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        if 'INPLACE' in ASM_INSTR[self.program[self.rip-1][0]]:
            self.pretty_print(f"{tos}.{name} {tos1}")
        else:
            self.pretty_print(f"{tos}.{name} = {tos1}")

    def DELETE_ATTR(self, val):
        # Functionality
        tos = self.pop()
        name = self.names[val]
        del tos.name

        # Decompilation
        tos = self.ppop()
        self.pretty_print(f"del {tos}.{name}")

    # TODO: figure out how to implement CLOSUREs
    def LOAD_CLOSURE(self, val):
        raise self.CodeError('unknown', 'Closures have not been implemented yet!')

    def LOAD_DEREF(self, val):
        raise self.CodeError('unknown', 'Closures have not been implemented yet!')

    def STORE_DEREF(self, val):
        raise self.CodeError('unknown', 'Closures have not been implemented yet!')

    def DELETE_DEREF(self,val):
        raise self.CodeError('unknown', 'Closures have not been implemented yet!')

    def LOAD_CLASSDEREF(self, val):
        raise self.CodeError('unknown', 'Closures have not been implemented yet!')

    def UNPACK_SEQUENCE(self, val):
        # Functionality
        tos = self.pop()
        sequence = tos[:val]
        for v in reversed(sequence):
            self.push(v)

        # Decompilation
        tos = self.ppop()
        for v in reversed(range(val)):
             self.ppush(f"{tos}[{v}]")
        self.pretty_print('')

    def UNPACK_EX(self, val):
        # Functionality
        tos = self.pop()
        high_byte = (val >> 8) & 0xFF
        low_byte = val & 0xFF
        before = tos[:low_byte]
        listed = tos[low_byte:-high_byte]
        after = tos[-high_byte:]
        for i in reversed(after):
            self.push(i)
        self.push(listed)
        for i in reversed(before):
            self.push(i)

        # Decompilation
        tos = self.ppop()
        for i in range(len(tos)-1,len(tos)-high_byte-1,-1):
             self.ppush(f"{tos}[{i}]")
        self.ppush(f"{tos}[{low_byte}:-{high_byte}]")
        for i in range(low_byte-1,-1,-1):
             self.ppush(f"{tos}[{i}]")
        self.pretty_print('')

    def PRINT_EXPR(self, val):
        # Functionality
        tos = self.pop()
        tos # Prints only if in interactive mode

        # Decompilation
        tos = self.ppop()
        self.pretty_print(tos)

    def BUILD_SLICE(self, val):
        # Functionality
        match val:
            case 2:
                tos = self.pop()
                tos1 = self.pop()
                self.push(slice(tos1,tos))
            case 3:
                tos = self.pop()
                tos1 = self.pop()
                tos2 = self.pop()
                self.push(slice(tos2,tos1,tos))
            case _:
                raise self.CodeError('known-error', "BUILD_SLICE was provided " + str(val) + " when argc can only be 2 or 3")

        # Decompilation
        match val:
            case 2:
                tos = self.ppop()
                tos1 = self.ppop()
                self.ppush(f"slice({tos1},{tos})")
            case 2:
                tos = self.ppop()
                tos1 = self.ppop()
                tos2 = self.ppop()
                self.ppush(f"slice({tos2},{tos1},{tos})")
        self.pretty_print('')

    def LOAD_BUILD_CLASS(self, val):
        # Functionality
        self.push(builtins.__build_class__())  # Will be popped by CALL_FUNCTION to construct a class

        # Decompilation
        self.ppush('builtins.__build_class__()')
        self.pretty_print('')

    def LOAD_ASSERTION_ERROR(self, val):
        # Functionality
        self.push(AssertionError)

        # Decompilation
        self.ppush('AssertionError')
        self.pretty_print('')

    def YIELD_FROM(self, val):
        # Decompilation
        self.pretty_print(f"yield from {self.ppop()}")

        # Functionality
        tos = self.pop()
        yield from tos

    def FORMAT_VALUE(self, val):
        # Functionality
        fmt_spec = ''
        if (val & 0x04) == 0x04:
            fmt.spec = self.pop()

        value = self.pop()
        match val & 0x03:
            case 0x00: value = value
            case 0x01: value = str(value)
            case 0x02: value = repr(value)
            case 0x03: value = ascii(value)

        self.push(format(value, fmt_spec))

        # Decompilation
        tos = self.ppop()
        tos1 = self.ppop()
        match val & 0x03:
            case 0x00: tos1 = tos1
            case 0x01: tos1 = f"str({tos1})"
            case 0x02: tos1 = f"repr({tos1})"
            case 0x03: tos1 = f"ascii({tos1})"
        self.ppush(f"format({tos1}, {tos})")
        self.pretty_print('')

    def LOAD_METHOD(self, val):
        # Functionality
        obj = self.pop()
        name = self.names[val]
        try:
            attr = getattr(obj, name)
            if hasattr(attr, '__self__') and attr.__self__ is obj:
                self.push(attr.__func__)
                self.push(obj)
            else:
                self.push(None)
                self.push(attr)
        except:
            self.push(None)
            self.push(None)        

        # Decompilation
        self.ppush(name)
        self.pretty_print('')
               

    def CALL_METHOD(self, val):
        # Functionality
        args = [self.pop() for _ in range(val)]
        args.reverse()
        obj = self.pop()
        method = self.pop()

        if obj is not None:
            self.push(method(obj, *args))
        else:
            self.push(method(*args))

        # Decompilation
        args = reversed([self.ppop() for _ in range(val)])
        obj = self.ppop()
        method = self.ppop()
        self.ppush(f"{obj}.{method}({', '.join(args)})")

    def MAKE_FUNCTION(self, val):
        # Functionality
        name = self.pop()
        code = self.pop()

        # Initialize function metadata
        defaults = None
        kw_defaults = None
        annotations = None
        closure = None

        if flags & 0x08:
            closure = self.pop() # Tuple of cells
        if flags & 0x04:
            annotations = self.pop() # Tuple of annotations
        if flags & 0x02:
            kw_defaults = self.pop() # Dict of kw-only defaults
        if flags & 0x01:
            defaults = self.pop() # Tuple of positional defaults

        func = types.FunctionType(code, name, closure=closure, defaults=defaults)
        func.__kwdefaults__ = kw_defaults
        func.__annotations__ = annotations

        self.push(func)

        # Decompilation
        name = self.ppop()
        code = self.ppop()

        # Initialize function metadata
        defaults = 'None'
        kw_defaults = 'None'
        annotations = 'None'
        closure = 'None'

        if flags & 0x08:
            closure = self.ppop() # Tuple of cells
        if flags & 0x04:
            annotations = self.ppop() # Tuple of annotations
        if flags & 0x02:
            kw_defaults = self.ppop() # Dict of kw-only defaults
        if flags & 0x01:
            defaults = self.ppop() # Tuple of positional defaults

        self.ppush(f"types.FunctionType({code}, {name}, closure={closure}, defaults={defaults}, kwdefaults={kw_defaults}, annotations={annotations})")

    def CALL_FUNCTION(self, val, preface=''):
        # Functionality
        argv = [self.pop() for _ in range(val)]
        argv.reverse()
        func_name = self.pop()
        func = getattr(builtins, func_name)

        try:
            if func:
                if func_name == 'type':
                    self.push(func(*argv).__name__)
                else:
                    self.push(func(*argv))
        except Exception as e:
            self.push(None)
            raise self.CodeError('known-error', "The called function "+func.__name__+" encountered an exception: " + e.args[0])

        # Decompilation
        argv = [self.ppop() for _ in range(val)]
        argv.reverse()
        func_name = self.ppop()
        self.ppush(f"{preface}{func_name}({', '.join(argv)})")
        self.pretty_print('')

    def CALL_FUNCTION_KW(self, val, preface=''):
        # Functionality
        kw_names = self.pop()
        kw_values = [self.pop() for _ in range(len(kw_names))]
        kw_values.reverse()  # TODO: Figure out if the order of the kw_values is correct
        kwargs = dict(zip(kw_names, kw_values))

        num_args = val - len(kw_names)
        args = [self.pop() for _ in range(len(num_args))]
        args.reverse()

        func = self.pop()
        self.push(func(*args, **kwargs))

        # Decompilation
        kw_names = self.ppop()
        kw_names.reverse()
        kw_vals = [f"{n}:{self.ppop()}" for n in kw_names]
        kw_vals.reverse()
        args = [self.ppop() for _ in range(len(num_args))]
        args.reverse()
        func = self.ppop()
        self.ppush(f"{preface}{func_name}({', '.join(args)}, {', '.join(kw_vals)}")
        self.pretty_print('')

    def CALL_FUNCTION_EX(self, val, preface=''):
        # Functionality
        if val & 1 == 0:
            kwargs = self.pop()
            args = self.pop()
            func = self.pop()
            self.push(func(*args, **kwargs))
        else:
            args = self.pop()
            func = self.pop()
            self.push(func(*args))

        # Decompilation
        if val & 1 == 0:
            kwargs = self.ppop()
            args = self.ppop()
            func_name = self.ppop()
            self.ppush(f"{preface}{func_name}({', '.join(args)}, {', '.join(kwargs)})")
        else:
            args = self.ppop()
            func_name = self.ppop()
            self.ppush(f"{preface}{func_name}({', '.join(args)})")
        self.pretty_print('')

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
                        if self.rbp == 0:
                            return
                        block = self.bpop()
                        self.rip = block.addr+1
                        self.rbp += 1 # you don't actually pop
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
        self.rpp = 0
        self.variables = self.og_variables.copy()
        self.constants = self.og_constants.copy()
        self.globals = self.og_globals.copy()
        self.names = self.og_names.copy()
        self.program = self.og_program.copy()
        for i in range(1,len(command)):
            self.variables[i-1] = command[i]

    def run(self, command):
        self.reset(command)
        self.cont(-1)


    def tui(self):
        while True:
            command = parse_input(input("> "))
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
                            case 'name':
                                idx = int(command[2])
                                self.names[idx] = eval(command[3])
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
                                s = 0
                                e = 0
                                match len(command):
                                    case 2: 
                                        s = 0
                                        e = len(self.program)
                                    case 3: 
                                        s = int(command[2])
                                        e = s+1
                                    case 4: 
                                        s = int(command[2])
                                        e = int(command[3])
                                    case _: print("Command is not recognized")

                                for i in range(s,e):
                                    preface = " *" if i == self.rip else "  "
                                    last = f"({self.program[i][1]})"
                                    print(f"{preface:<2} {i:<3}: {ASM_INSTR[self.program[i][0]]:<25} {last:<4}     {self.pretty_program[i]}")
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
test_code = Code(bytes.fromhex('64017c0037007d00740064027c0064031a0083027d027a067c007c0216007d0257006e1e04007401792f01007d0301007a127c0164046b0272245700590064007d037e03640553005700590064007d037e036406530064007d037e03770177007c0064076b05724d7c00740274037c0183018301160064026b02724b740474057c01830174036b0272487c01830153006408830153006406530074037c01830174067c00830117005300'), ['', '', '', ''], [None,83,0,97,'cat','/','',123,'0'], ['max','Exception','len','str','eval','type','chr'], [])
test_code.tui()
