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
  0x7a: "JUMP_ABSOLUTE",
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
        self.og_program = disassemble(bytecode)
        self.program = []
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

    def ROT_TWO(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos)
        self.push(tos1)

    def ROT_THREE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        tos2 = self.pop()
        self.push(tos)
        self.push(tos2)
        self.push(tos1)

    def ROT_FOUR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        tos2 = self.pop()
        tos3 = self.pop()
        self.push(tos)
        self.push(tos3)
        self.push(tos2)
        self.push(tos1)

    def ROT_N(self, val):
        tos = [self.pop() for _ in range(val)]
        self.push(tos[0])
        for i in range(val-1, 0, -1):
            self.push(tos[i])

    def NOP(self, val):
        return

    def EXTENDED_ARG(self, val):
        if self.rip >= len(self.program)-1:
            raise Self.CodeError('known-error', 'EXTENDED_ARG is the last instruction')
        combined = val << 8 | self.program[self.rip+1][1]
        self.program[self.rip+1][1] = combined

    # Typically used in preparation of Error-handling, since restoring the exception state requires multiple values to be popped
    def DUP_TOP(self, val):
        tos = self.pop()
        self.push(tos)
        self.push(tos)

    def DUP_TOP_TWO(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1)
        self.push(tos)
        self.push(tos1)
        self.push(tos)

    def UNARY_POSITIVE(self, val):
        tos = self.pop()
        self.push(+tos)

    def UNARY_NEGATIVE(self, val):
        tos = self.pop()
        self.push(-tos)

    def UNARY_NOT(self, val):
        tos = self.pop()
        self.push(not tos)

    def UNARY_INVERT(self, val):
        tos = self.pop()
        self.push(~tos)

    def BINARY_MATRIX_MULTIPLY(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 * tos)

    def INPLACE_MATRIX_MULTIPLY(self, val):
        self.BINARY_MATRIX_MULTIPLY(val)

    def BINARY_POWER(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 ** tos)

    def INPLACE_POWER(self, val):
        self.BINARY_POWER(val)

    def BINARY_MULTIPLY(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 * tos)

    def INPLACE_MULTIPLY(self, val):
        self.BINARY_MULTIPLY(val)

    def BINARY_MODULO(self, val):
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 % tos)
        except:
            self.push(self.rip)
            self.push(None)
            self.push(Exception)
            raise self.CodeError('known-error', 'Attempted to do modulo by a non-negative number')

    def INPLACE_MODULO(self, val):
        self.BINARY_MODULO(val)
    
    def BINARY_ADD(self, val):
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 + tos)
        except:
            self.push(None)
            raise self.CodeError('known-error', "Values "+str(tos1)+" and "+str(tos)+" cannot be added together")

    def INPLACE_ADD(self, val):
        self.BINARY_ADD(val)

    def BINARY_SUBTRACT(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 - tos)

    def INPLACE_SUBTRACT(self, val):
        self.BINARY_SUBTRACT(val)

    def BINARY_SUBSCR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1[tos])

    def STORE_SUBSCR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        tos2 = self.pop()
        tos1[tos] = tos2
        # TODO: Figure out how tos1 is preserved

    def DELETE_SUBSCR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        del tos1[tos]
        # TODO: Figure out how tos1 is preserved

    def BINARY_FLOOR_DIVIDE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        try:
            self.push(tos1 // tos)
        except:
            self.push(None)
            raise self.CodeError('known-error', 'Division by 0 occurred.')
        
    def INPLACE_FLOOR_DIVIDE(self, val):
        self.BINARY_FLOOR_DIVIDE(val)

    def BINARY_TRUE_DIVIDE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 / tos)

    def INPLACE_TRUE_DIVIDE(self, val):
        self.BINARY_TRUE_DIVIDE(val)

    def BINARY_LSHIFT(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 << tos)

    def INPLACE_LSHIFT(self, val):
        self.BINARY_LSHIFT(val)

    def BINARY_RSHIFT(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 >> tos)

    def INPLACE_RSHIFT(self, val):
        self.BINARY_RSHIFT(val)

    def BINARY_AND(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 & tos)

    def INPLACE_AND(self, val):
        self.BINARY_AND(val)

    def BINARY_XOR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 ^ tos)

    def INPLACE_XOR(self, val):
        self.BINARY_XOR(val)

    def BINARY_OR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        self.push(tos1 | tos)

    def INPLACE_OR(self, val):
        self.BINARY_OR(val)

    def GET_LEN(self, val):
        tos = self.pop()
        self.push(len(tos))

    def MATCH_MAPPING(self, val):
        tos = self.pop()
        self.push(isinstance(tos, abc.Mapping))

    def MATCH_SEQUENCE(self, val):
        tos = self.pop()
        self.push(isinstance(tos, abc.Sequence))

    def MATCH_KEYS(self, val):
        tos = self.pop()
        tos1 = self.pop()
        lookups = ()
        for item in tos:
            if item not in tos1:
                self.push(None)
                return
            lookups += (tos1[item],)
        self.push(lookups)

    def MATCH_CLASS(self, val):
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

    def COPY_DICT_WITHOUT_KEYS(self, val):
        keys = self.pop()
        old_dict = self.pop()
        new_dict = {k: v for k, v in old_dict.items() if k not in keys}
        self.push(new_dict) 

    def SETUP_WITH(self, val):
        self.push(getattr(self, '__exit__'))
        self.bpush(self.Block(val))
        result = self.__enter__()
        self.push(result)

    # Handles an exception in a with statement
    def WITH_EXCEPT_START(self, val):
        self.CALL_FUNCTION(3)

    # TODO: figure out what to do with the value from the generator
    async def GEN_START(self, val):
        tos = self.pop()
        match val:
            case 0: next(tos)
            case 1: await tos
            case 2: await anext(tos)

    def LIST_TO_TUPLE(self, val):
        tos = self.pop()
        self.push(tuple(tos))

    def BUILD_TUPLE(self, val):
        self.push(reversed(tuple(self.pop() for _ in range(val))))

    def BUILD_LIST(self, val):
        self.push(reversed([self.pop() for _ in range(val)]))

    def BUILD_SET(self, val):
        self.push({self.pop() for _ in range(val)})

    def BUILD_MAP(self, val):
        pairs = []
        for _ in range(val):
            v = self.pop()
            k = self.pop()
            pairs.append((k,v))
        self.push(dict(reversed(pairs)))

    def BUILD_CONST_KEY_MAP(self, val):
        keys = self.pop()
        values = [self.pop() for _ in range(val)]
        values.reverse()
        self.push({keys[i]:values[i] for i in range(val)})

    def BUILD_STRING(self, val):
        value = ''
        for _ in range(val):
            value = self.pop() + value
        self.push(value)

    def RETURN_VALUE(self, val):
        raise self.CodeError('return', self.pop())

    def RERAISE(self, val):
        raise self.CodeError('known-error', self.pop())

    def RAISE_VARARGS(self, val):
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
        tos = self.pop()
        yield tos

    # from tos import *
    def IMPORT_STAR(self, val):
        tos = self.pop()
        names = getattr(tos, '__all__', tos.__dict__.keys())
        for name in names:
            self.current_namespace[name] = getattr(tos, name)

    def IMPORT_NAME(self, val):
        fromlist = self.pop()
        level = self.pop()
        name = self.names[val]
        module = __import__(name, globals=self.globals, locals=self.locals, fromlist=fromlist, level=level)
        self.push(module)

    # Typically followed by STORE_FAST
    def IMPORT_FROM(self, val):
        module = self.pop()
        name = self.names[val]
        v = getattr(module, name)
        self.push(v)

    def SETUP_ANNOTATIONS(self, val):
        if '__annotations__' not in self.locals():
            self.locals['__annotations__'] = {}

    def GET_AITER(self, val):
        tos = self.pop()
        self.push(tos.__aiter__())

    def GET_ANEXT(self, val):
        tos = self.pop()
        self.push(tos.__anext__())
        self.GET_AWAITABLE(val)

    def GET_AWAITABLE(self, val):
        tos = self.pop()
        self.push(get_awaitable(tos))

    def GET_ITER(self, val):
        tos = self.pop()
        self.push(iter(tos))

    def GET_YIELD_FROM_ITER(self, val):
        tos = self.pop()
        if inspect.isgenerator(tos) or inspect.iscoroutine(tos):
            self.push(tos)
        else:
            self.push(iter(tos))

    def FOR_ITER(self, val):
        tos = self.pop()
        try:
            v = tos.__next__()
            self.push(tos)
            self.push(v)
        except:
            self.rip += val

    def LIST_APPEND(self, val):
        tos = self.pop()
        tos1 = self.pop()
        list.append(tos1[-val],tos)

    def LIST_EXTEND(self, val):
        tos = self.pop()
        tos1 = self.pop()
        list.extend(tos1[-val],tos)

    def SET_ADD(self, val):
        tos = self.pop()
        tos1 = self.pop()
        set.add(tos1[-val],tos)

    def SET_UPDATE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        set.update(tos1[-val],tos)

    def DICT_MERGE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        duplicates = tos1[-val].keys() & tos.keys()
        if duplicates:
            raise CodeError('known-error', "Duplicate keys " + duplicates + " were found during DICT_MERGE")
        dict.update(tos1[-val],tos)

    def DICT_UPDATE(self, val):
        tos = self.pop()
        tos1 = self.pop()
        dict.update(tos1[-val],tos)

    def MAP_ADD(self, val):
        tos = self.pop()
        tos1 = self.pop()
        dict.__setitem__(tos1[-val],tos1,tos)

    def BEFORE_ASYNC_WITH(self, val):
        tos = self.pop()
        self.push(tos.__aexit__)
        self.push(tos.__aenter__())

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
        tos = self.pop()
        tos1 = self.pop()
        if val == 1:
            self.push(tos1 is not tos)
        else:
            self.push(tos1 is tos)

    def CONTAINS_OP(self, val):
        tos = self.pop()
        tos1 = self.pop()
        if val == 1:
            self.push(tos1 not in tos)
        else:
            self.push(tos1 in tos)

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

    def JUMP_ABSOLUTE(self, val):
        self.rip = val - 1

    def JUMP_IF_FALSE_OR_POP(self, val):
        tos = self.pop()
        if tos == False:
            self.rip = val - 1
            self.push(tos)

    def JUMP_IF_TRUE_OR_POP(self, val):
        tos = self.pop()
        if tos == True:
            self.rip = val - 1
            self.push(tos)

    def POP_JUMP_IF_FALSE(self, val):
        tos = self.pop()
        if tos == False:
            self.rip = val - 1

    def POP_JUMP_IF_TRUE(self, val):
        tos = self.pop()
        if tos == True:
            self.rip = val - 1

    def JUMP_IF_NOT_EXC_MATCH(self, val):
        tos = self.pop()
        tos1 = self.pop()
        if type(tos1) is type(tos):
            self.rip = val - 1 

    def SETUP_FINALLY(self, val):
        self.bpush(self.Block(val+self.rip))

    def LOAD_CONST(self, val):
        self.push(self.constants[val])

    def LOAD_GLOBAL(self, val):
        self.push(self.globals[val])

    def STORE_GLOBAL(self, val):
        self.globals[val] = self.pop()

    def DELETE_GLOBAL(self, val):
        del self.globals[val]

    def LOAD_FAST(self, val):
        self.push(self.variables[val])

    def STORE_FAST(self, val):
        self.variables[val] = self.pop()

    def DELETE_FAST(self, val):
        del self.variables[val]

    def LOAD_NAME(self, val):
        self.push(self.names[val])

    def STORE_NAME(self, val):
        self.names[val] = self.pop()

    def DELETE_NAME(self, val):
        del self.names[val]

    def LOAD_ATTR(self, val):
        tos = self.pop()
        self.push(getattr(tos, self.names[val]))

    def STORE_ATTR(self, val):
        tos = self.pop()
        tos1 = self.pop()
        name = self.names[val]
        setattr(tos, name, tos1)

    def DELETE_ATTR(self, val):
        tos = self.pop()
        name = self.names[val]
        del tos.name

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
        tos = self.pop()
        sequence = tos[:val]
        for v in reversed(sequence):
            self.push(v)

    def UNPACK_EX(self, val):
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

    def PRINT_EXPR(self, val):
        tos = self.pop()
        tos # Prints only if in interactive mode

    def BUILD_SLICE(self, val):
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

    def LOAD_BUILD_CLASS(self, val):
        self.push(builtins.__build_class__())  # Will be popped by CALL_FUNCTION to construct a class

    def LOAD_ASSERTION_ERROR(self, val):
        self.push(AssertionError)

    def YIELD_FROM(self, val):
        tos = self.pop()
        yield from tos

    def FORMAT_VALUE(self, val):
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

    def LOAD_METHOD(self, val):
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

    def CALL_METHOD(self, val):
        args = [self.pop() for _ in range(val)]
        args.reverse()
        obj = self.pop()
        method = self.pop()

        if obj is not None:
            self.push(method(obj, *args))
        else:
            self.push(method(*args))

    def MAKE_FUNCTION(self, val):
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

    def CALL_FUNCTION(self, val):
        argv = [None for _ in range(val)]
        for i in range(val-1, -1, -1):
            argv[i] = self.pop()
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

    def CALL_FUNCTION_KW(self, val):
        kw_names = self.pop()
        kw_values = [self.pop() for _ in range(len(kw_names))]
        kw_values.reverse()  # TODO: Figure out if the order of the kw_values is correct
        kwargs = dict(zip(kw_names, kw_values))

        num_args = val - len(kw_names)
        args = [self.pop() for _ in range(len(num_args))]
        args.reverse()

        func = self.pop()
        self.push(func(*args, **kwargs))

    def CALL_FUNCTION_EX(self, val):
        if val & 1 == 0:
            kwargs = self.pop()
            args = self.pop()
            func = self.pop()
            self.push(func(*args, **kwargs))
        else:
            args = self.pop()
            func = self.pop()
            self.push(func(*args))

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
                                    print(preface,i,":", ASM_INSTR[self.program[i][0]], "(", self.program[i][1], ")")
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
