'''
Python Type Inferencer and Flow Analyzer (TIFA)
 
TIFA uses a number of simplifications of the Python language.
  * Variables cannot change type
  * Variables cannot be deleted
  * Complex types have to be homogenous
  * No introspection or reflective characteristics
  * No dunder methods
  * No closures (maybe?)
  * You cannot write a variable out of scope
  * You cannot read a mutable variable out of scope
  * No multiple inheritance
  
Additionally, it reads the following as issues:
  * Cannot read a variable without having first written to it.
  * Cannot rewrite a variable unless it has been read.
  
Important concepts:
    Issue: A problematic situation in the submitted code that will be reported
           but may not stop the execution.
    Error: A situation in execution that terminates the program.
    Name: A name of a variable
    Scope: The context of a function, with its own namespaces. Represented
           internally using numeric IDs (Scope IDs).
    Scope Chain: A stack of scopes, with the innermost scope on top.
    Fully Qualified Name: A string representation of a variable and its scope
                          chain, written using "/". For example:
                          0/1/4/my_variable_name
    Path: A single path of execution through the control flow; every program
          has at least one sequential path, but IFs, FORs, WHILEs, etc. can
          cause multiple paths. Paths are represented using numeric IDs (Path
          IDs).
    State: Information about a Name that indicates things like the variable's
           current type and whether that name has been read, set, or
           overwritten.
    Identifier: A wrapper around variables, used to hold their potential
                non-existence (which is an Issue but not an Error).
    Type: A symbolic representation of the variable's type.
    Literal: Sometimes, we need a specialized representation of a literal value
             to be passed around. This is particularly important for accessing
             elements in an tuples.
'''

import ast

def _dict_extends(d1, d2):
    d3 = {}
    for key, value in d1.items():
        d3[key] = value
    for key, value in d2.items():
        d3[key] = value
    return d3

class Type:
    '''
    Parent class for all other types, used to provide a common interface.
    
    TODO: Handle more complicated object-oriented types and custom types
    (classes).
    '''
    fields = {}
    def clone(self):
        return self.__class__()
    def index(self, i):
        return self.clone()
    def load_attr(self, attr, tifa, callee=None, callee_position=None):
        if attr in self.fields:
            return self.fields[attr]
        # TODO: Handle more kinds of common mistakes
        if attr == "append":
            tifa.report_issue('Append to non-list', 
                              {'name': tifa.identifyCaller(callee), 
                               'position': callee_position, 'type': self})
        return UnknownType()
    

class UnknownType(Type):
    '''
    A special type used to indicate an unknowable type.
    '''

class RecursedType(Type):
    '''
    A special type used as a placeholder for the result of a
    recursive call that we have already process. This type will
    be dominated by any actual types, but will not cause an issue.
    '''

class FunctionType(Type):
    '''
    
    Special values for `returns`:
        identity: Returns the first argument's type
        element: Returns the first argument's first element's type
        void: Returns the NoneType
    '''
    def __init__(self, definition=None, name="*Anonymous", returns=None):
        if returns is not None and definition is None:
            if returns == 'identity':
                def definition(ti, ty, na, args, ca):
                    if args:
                        return args[0].clone()
                    return UnknownType()
            elif returns == 'element':
                def definition(ti, ty, na, args, ca):
                    if args:
                        return args[0].index(0)
                    return UnknownType()
            elif returns == 'void':
                def definition(ti, ty, na, args, ca):
                    return NoneType()
            else:
                def definition(ti, ty, na, args, ca):
                    return returnType.clone()
        self.definition = definition
        self.name = name
        
class NumType(Type):
    pass
    
class NoneType(Type):
    pass
    
class BoolType(Type):
    pass

class TupleType(Type):
    '''
    '''
    def __init__(self, subtypes=None):
        if subtypes is None:
            subtypes = []
        self.subtypes = subtypes
    def index(self, i):
        if isinstance(i, LiteralNum):
            return self.subtypes[i.value].clone()
        else:
            return self.subtypes[i].clone()
    def clone(self):
        return TupleType([t.clone() for t in self.subtypes])

class ListType(Type):
    def __init__(self, subtype=None, empty=True):
        if subtype is None:
            subtype = UnknownType()
        self.subtype = subtype
        self.empty = empty
    def index(self, i):
        return self.subtype.clone()
    def clone(self):
        return ListType(self.subtype.clone(), self.empty)
    def load_attr(self, attr, tifa, callee=None, callee_position=None):
        if attr == 'append':
            def _append(tifa, function_type, callee, args, position):
                if args:
                    if callee:
                        tifa.append_variable(callee, ListType(args[0].clone()), 
                                             position)
                    self.empty = False
                    self.subtype = args[0]
            return FunctionType(_append, 'append')
        return super().load_attr(attr, tifa, callee, callee_position)

class StrType(Type):
    def index(self, i):
        return StrType()
    fields = _dict_extends(Type.fields, {})

StrType.fields.update({
    # Methods that return strings
    "capitalize": FunctionType('capitalize', returns=StrType()),
    "center": FunctionType('center', returns=StrType()),
    "expandtabs": FunctionType('expandtabs', returns=StrType()),
    "join": FunctionType('join', returns=StrType()),
    "ljust": FunctionType('ljust', returns=StrType()),
    "lower": FunctionType('lower', returns=StrType()),
    "lstrip": FunctionType('lstrip', returns=StrType()),
    "replace": FunctionType('replace', returns=StrType()),
    "rjust": FunctionType('rjust', returns=StrType()),
    "rstrip": FunctionType('rstrip', returns=StrType()),
    "strip": FunctionType('strip', returns=StrType()),
    "swapcase": FunctionType('swapcase', returns=StrType()),
    "title": FunctionType('title', returns=StrType()),
    "translate": FunctionType('translate', returns=StrType()),
    "upper": FunctionType('upper', returns=StrType()),
    "zfill": FunctionType('zfill', returns=StrType()),
    # Methods that return numbers
    "count": FunctionType('count', returns=NumType()),
    "find": FunctionType('find', returns=NumType()),
    "rfind": FunctionType('rfind', returns=NumType()),
    "index": FunctionType('index', returns=NumType()),
    "rindex": FunctionType('rindex', returns=NumType()),
    # Methods that return booleans
    "startswith": FunctionType('startswith', returns=BoolType()),
    "endswith": FunctionType('endswith', returns=BoolType()),
    "isalnum": FunctionType('isalnum', returns=BoolType()),
    "isalpha": FunctionType('isalpha', returns=BoolType()),
    "isdigit": FunctionType('isdigit', returns=BoolType()),
    "islower": FunctionType('islower', returns=BoolType()),
    "isspace": FunctionType('isspace', returns=BoolType()),
    "istitle": FunctionType('istitle', returns=BoolType()),
    "isupper": FunctionType('isupper', returns=BoolType()),
    # Methods that return List of Strings
    "rsplit": FunctionType('rsplit', returns=ListType(StrType())),
    "split": FunctionType('split', returns=ListType(StrType())),
    "splitlines": FunctionType('splitlines', returns=ListType(StrType()))
})
class FileType(Type):
    def index(self, i):
        return StrType()
    fields = _dict_extends(Type.fields, {
        'close': FunctionType('close', returns='void'),
        'read': FunctionType('read', returns=StrType()),
        'readlines': FunctionType('readlines', returns=ListType(StrType(), False))
    })
    
class DictType(Type):
    def __init__(self, empty=False, literals=None, keys=None, values=None):
        self.empty = empty
        self.literals = literals
        self.values = values
        self.keys = keys
    def index(self, i):
        if self.literals is not None:
            for literal, value in zip(self.literals, self.values):
                if Tifa.are_literals_equal(literal, i):
                    return value.clone()
            return UnknownType()
        else:
            return self.keys.clone()
    def load_attr(self, attr, tifa, callee=None, callee_position=None):
        if attr == 'items':
            def _items(tifa, function_type, callee, args, position):
                if type.literals is None:
                    return ListType(TupleType([self.keys, self.values]))
                else:
                    return ListType(TupleType([self.literals[0].type(),
                                               self.values[0]]))
            return FunctionType(_items, 'items')
        elif attr == 'keys':
            def _keys(tifa, function_type, callee, args, position):
                if type.literals is None:
                    return ListType(self.keys)
                else:
                    return ListType(self.literals[0].type())
            return FunctionType(_keys, 'keys')
        elif attr == 'values':
            def _items(tifa, function_type, callee, args, position):
                if type.literals is None:
                    return ListType(self.values)
                else:
                    return ListType(self.values[0])
            return FunctionType(_values, 'values')
        return super().load_attr(attr, tifa, callee, callee_position)

class ModuleType(Type):
    def __init__(self, name="*UnknownModule", submodules=None, fields=None):
        self.name = name
        if submodules is None:
            submodules = {}
        self.submodules = submodules
        if fields is None:
            fields = {}
        self.fields = fields

class SetType(ListType):
    pass

class GeneratorType(ListType):
    pass

# Custom parking class in blockpy    
class TimeType(Type): pass
class DayType(Type): pass
    
MODULES = {
    'matplotlib': ModuleType('matplotlib',
        submodules={
            'pyplot': ModuleType('pyplot', fields={
                'plot': FunctionType(name='plot', returns=NoneType()),
                'hist': FunctionType(name='hist', returns=NoneType()),
                'scatter': FunctionType(name='scatter', returns=NoneType()),
                'show': FunctionType(name='show', returns=NoneType()),
                'xlabel': FunctionType(name='xlabel', returns=NoneType()),
                'ylabel': FunctionType(name='ylabel', returns=NoneType()),
                'title': FunctionType(name='title', returns=NoneType()),
            })
        }),
    'pprint': ModuleType('pprint',
        fields={
            'pprint': FunctionType(name='pprint', returns=NoneType())
        }),
    'random': ModuleType('random',
        fields={
            'randint': FunctionType(name='randint', returns=NumType())
        }),
    'turtle': ModuleType('turtle',
        fields={
            'forward': FunctionType(name='forward', returns=NoneType()),
            'backward': FunctionType(name='backward', returns=NoneType()),
            'color': FunctionType(name='color', returns=NoneType()),
            'right': FunctionType(name='right', returns=NoneType()),
            'left': FunctionType(name='left', returns=NoneType()),
        }),
    'parking': ModuleType('parking',
        fields={
            'Time': FunctionType(name='Time', returns=TimeType()),
            'now': FunctionType(name='now', returns=TimeType()),
            'Day': FunctionType(name='Day', returns=DayType()),
            'today': FunctionType(name='today', returns=DayType()),
        }),
    'math': ModuleType('math',
        fields={
            'ceil': FunctionType(name='ceil', returns=NumType()),
            'copysign': FunctionType(name='copysign', returns=NumType()),
            'fabs': FunctionType(name='fabs', returns=NumType()),
            'factorial': FunctionType(name='factorial', returns=NumType()),
            'floor': FunctionType(name='floor', returns=NumType()),
            'fmod': FunctionType(name='fmod', returns=NumType()),
            'frexp': FunctionType(name='frexp', returns=NumType()),
            'fsum': FunctionType(name='fsum', returns=NumType()),
            'gcd': FunctionType(name='gcd', returns=NumType()),
            'isclose': FunctionType(name='isclose', returns=BoolType()),
            'isfinite': FunctionType(name='isfinite', returns=BoolType()),
            'isinf': FunctionType(name='isinf', returns=BoolType()),
            'isnan': FunctionType(name='isnan', returns=BoolType()),
            'ldexp': FunctionType(name='ldexp', returns=NumType()),
            'modf': FunctionType(name='modf', returns=NumType()),
            'trunc': FunctionType(name='trunc', returns=NumType()),
            'log': FunctionType(name='log', returns=NumType()),
            'log1p': FunctionType(name='log1p', returns=NumType()),
            'log2': FunctionType(name='log2', returns=NumType()),
            'log10': FunctionType(name='log10', returns=NumType()),
            'pow': FunctionType(name='pow', returns=NumType()),
            'sqrt': FunctionType(name='sqrt', returns=NumType()),
            'acos': FunctionType(name='acos', returns=NumType()),
            'sin': FunctionType(name='sin', returns=NumType()),
            'cos': FunctionType(name='cos', returns=NumType()),
            'tan': FunctionType(name='tan', returns=NumType()),
            'asin': FunctionType(name='asin', returns=NumType()),
            'acos': FunctionType(name='acos', returns=NumType()),
            'atan': FunctionType(name='atan', returns=NumType()),
            'atan2': FunctionType(name='atan2', returns=NumType()),
            'hypot': FunctionType(name='hypot', returns=NumType()),
            'degrees': FunctionType(name='degrees', returns=NumType()),
            'radians': FunctionType(name='radians', returns=NumType()),
            'sinh': FunctionType(name='sinh', returns=NumType()),
            'cosh': FunctionType(name='cosh', returns=NumType()),
            'tanh': FunctionType(name='tanh', returns=NumType()),
            'asinh': FunctionType(name='asinh', returns=NumType()),
            'acosh': FunctionType(name='acosh', returns=NumType()),
            'atanh': FunctionType(name='atanh', returns=NumType()),
            'erf': FunctionType(name='erf', returns=NumType()),
            'erfc': FunctionType(name='erfc', returns=NumType()),
            'gamma': FunctionType(name='gamma', returns=NumType()),
            'lgamma': FunctionType(name='lgamma', returns=NumType()),
            'pi': NumType(),
            'e': NumType(),
            'tau': NumType(),
            'inf': NumType(),
            'nan': NumType(),
        }),
}

def _builtin_sequence_constructor(constructor):
    '''
    Helper function for creating constructors for the Set and List types.
    These constructors use the subtype of the arguments.
    
    Args:
        constructor (Type): A function for creating new sequence types.
    '''
    def sequence_call(tifa, function_type, callee, args, position):
    # TODO: Should inherit the emptiness too
        return_type = constructor(empty=True)
        if args:
            return_type.subtype = args[0].index(LiteralNum(0))
        return return_type
    return sequence_call
    
def _builtin_zip(tifa, function_type, callee, args, position):
    '''
    Definition of the built-in zip function, which consumes a series of
    sequences and returns a list of tuples, with each tuple composed of the
    elements of the sequence paired (or rather, tupled) together.
    '''
    if args:
        tupled_types = TupleType(subtypes=[])
        for arg in args:
            tupled_types.append(arg.index(0))
        return ListType(tupled_types)
    return ListType(empty=True)

BUILTINS = {
    # Void Functions
    "print": FunctionType(name="print", returns=NoneType()),
    # Math Functions
    "int": FunctionType(name="int", returns=NumType()),
    "abs": FunctionType(name="abs", returns=NumType()),
    "float": FunctionType(name="float", returns=NumType()),
    "len": FunctionType(name="len", returns=NumType()),
    "ord": FunctionType(name="ord", returns=NumType()),
    "pow": FunctionType(name="pow", returns=NumType()),
    "round": FunctionType(name="round", returns=NumType()),
    "sum": FunctionType(name="sum", returns=NumType()),
    # Boolean Functions
    "bool": FunctionType(name="bool", returns=BoolType()),
    "all": FunctionType(name="all", returns=BoolType()),
    "any": FunctionType(name="any", returns=BoolType()),
    "isinstance": FunctionType(name="isinstance", returns=BoolType()),
    # String Functions
    "input": FunctionType(name="input", returns=StrType()),
    "str": FunctionType(name="str", returns=StrType()),
    "chr": FunctionType(name="chr", returns=StrType()),
    "repr": FunctionType(name="repr", returns=StrType()),
    # File Functions
    "open": FunctionType(name="open", returns=FileType()),
    # List Functions
    "map": FunctionType(name="map", returns=ListType()),
    "list": FunctionType(name="list", 
                         definition=_builtin_sequence_constructor(ListType)),
    # Set Functions
    "list": FunctionType(name="list", 
                         definition=_builtin_sequence_constructor(SetType)),
    # Dict Functions
    "dict": FunctionType(name="dict", returns=DictType()),
    # Pass through
    "sorted": FunctionType(name="sorted", returns='identity'),
    "reversed": FunctionType(name="reversed", returns='identity'),
    "filter": FunctionType(name="filter", returns='identity'),
    # Special Functions
    "range": FunctionType(name="range", returns=ListType(NumType())),
    "dir": FunctionType(name="dir", returns=ListType(StrType())),
    "max": FunctionType(name="max", returns='element'),
    "min": FunctionType(name="min", returns='element'),
    "zip": FunctionType(name="zip", returns=_builtin_zip)
}
    
def merge_types(left, right):
    # TODO: Check that lists/sets have the same subtypes
    if isinstance(left, (ListType, SetType, GeneratorType)):
        if left.empty:
            return right.subtype
        else:
            return left.subtype.clone()
    elif isinstance(left, TupleType):
        return left.subtypes + right.subtypes
    
NumType_any = lambda *x: NumType
StrType_any = lambda *x: StrType
BoolType_any = lambda *x: BoolType
VALID_BINOP_TYPES = {
    ast.Add: {NumType: {NumType: NumType_any}, 
              StrType :{StrType: StrType_any}, 
              ListType: {ListType: merge_types},
              TupleType: {TupleType: merge_types}},
    ast.Sub: {NumType: {NumType: NumType_any}, 
              SetType: {SetType: merge_types}},
    ast.Div: {NumType: {NumType: NumType_any}},
    ast.FloorDiv: {NumType: {NumType: NumType_any}},
    ast.Mult: {NumType: {NumType: NumType_any, 
                     StrType: StrType_any, 
                     ListType: lambda l,r: r, 
                     TupleType: lambda l,r: r},
             StrType: {NumType: StrType_any},
             ListType: {NumType: lambda l,r: l},
             TupleType: {NumType: lambda l,r: l}},
    ast.Pow: {NumType: {NumType: NumType_any}},
    # TODO: Should we allow old-fashioned string interpolation?
    # Currently, I vote no because it makes the code harder and is bad form.
    ast.Mod: {NumType: {NumType: NumType_any}},
    ast.LShift: {NumType: {NumType: NumType_any}},
    ast.RShift: {NumType: {NumType: NumType_any}},
    ast.BitOr: {NumType: {NumType: NumType_any}, 
                BoolType: {NumType: NumType_any,
                         BoolType: BoolType_any}, 
                SetType: {SetType: merge_types}},
    ast.BitXor: {NumType: {NumType: NumType_any}, 
                BoolType: {NumType: NumType_any,
                         BoolType: BoolType_any}, 
                SetType: {SetType: merge_types}},
    ast.BitAnd: {NumType: {NumType: NumType_any}, 
                BoolType: {NumType: NumType_any,
                         BoolType: BoolType_any}, 
                SetType: {SetType: merge_types}}
}
VALID_UNARYOP_TYPES = {
    ast.UAdd: {NumType: NumType},
    ast.USub: {NumType: NumType},
    ast.Invert: {NumType: NumType}
}
    
def are_types_equal(left, right):
    '''
    Determine if two types are equal.
    
    This could be more Polymorphic - move the code for each type into
    its respective class instead.
    '''
    if left is None or right is None:
        return False
    elif isinstance(left, UnknownType) or isinstance(right, UnknownType):
        return False
    elif type(left) != type(right):
        return False
    elif isinstance(left, (GeneratorType, ListType)):
        if left.empty or right.empty:
            return True
        else:
            return are_types_equal(left.subtype, right.subtype)
    elif isinstance(left, TupleType):
        if left.empty or right.empty:
            return True
        elif len(left.subtypes) != len(right.subtypes):
            return False
        else:
            for l, r in zip(left.subtypes, right.subtypes):
                if not are_types_equal(l, r):
                    return False
            return True
    elif isinstance(left, DictType):
        if left.empty or right.empty:
            return True
        elif left.literals is not None and right.literals is not None:
            if len(left.literals) != len(right.literals):
                return False
            else:
                for l, r in zip(left.literals, right.literals):
                    if not are_types_equal(l, r):
                        return False
                for l, r in zip(left.values, right.values):
                    if not are_types_equal(l, r):
                        return False
                return True
        elif left.literals is not None or right.literals is not None:
            return False
        else:
            keys_equal = are_types_equal(left.keys, right.keys)
            values_equal = are_types_equal(left.values, right.values)
            return keys_equal and values_equal
    else:
        return True

class LiteralValue:
    '''
    A special literal representation of a value, used to represent access on
    certain container types.
    '''
    pass
    
class LiteralNum(LiteralValue):
    '''
    Used to capture indexes of containers.
    '''
    def __init__(self, value):
        self.value = value
    
    def type(self):
        return NumType()
        
class Identifier:
    '''
    A representation of an Identifier, encapsulating its current level of
    existence, scope and State.
    
    Attributes:
        exists (bool): Whether or not the variable actually is defined anywhere.
                       It is possible that a variable was retrieved that does
                       not actually exist yet, which indicates it might need to
                       be created.
        in_scope (bool): Whether or not the variable exists in the current
                         scope. Used to detect the presence of certain kinds
                         of errors where the user is using a variable from
                         a different scope.
        scoped_name (str): The fully qualified name of the variable, including
                           its scope chain.
        state (State): The current state of the variable.
    '''
    def __init__(self, exists, in_scope=False, scoped_name="UNKNOWN", state=""):
        self.exists = exists
        self.in_scope = in_scope
        self.scoped_name = scoped_name
        self.state = state

    
class State:
    '''
    A representation of a variable at a particular point in time of the program.
    
    Attributes:
        name (str): The name of the variable, without its scope chain
        trace (list of State): A recursive definition of previous States for
                               this State.
        type (Type): The current type of this variable.
        method (str): One of 'store', 'read', (TODO). Indicates the change that
                      occurred to this variable at this State.
        position (dict): A Position dictionary indicating where this State
                         change occurred in the source code.
        read (str): One of 'yes', 'no', or 'maybe'. Indicates if this variable
                    has been read since it was last changed. If merged from a
                    diverging path, it is possible that it was "maybe" read.
        set (str): One of 'yes', 'no', or 'maybe'. Indicates if this variable
                    has been set since it was last read. If merged from a 
                    diverging path, it is possible that it was "maybe" changed.
        over (str): One of 'yes', 'no', or 'maybe'. Indicates if this variable
                    has been overwritten since it was last set. If merged from a 
                    diverging path, it is possible that it was "maybe" changed.
        over_position (dict): A Position indicating where the State was
                              previously set versus when it was overwritten.
        
    '''
    def __init__(self, name, trace, type, method, position, 
                 read='maybe', set='maybe', over='maybe', over_position=None):
        self.name = name
        self.trace = trace
        self.type = type
        self.method = method
        self.position = position
        self.over_position = over_position
        self.read = read
        self.set = set
        self.over = over
    
    def copy(self, method, position):
        '''
        Make a copy of this State, copying this state into the new State's trace
        '''
        return State(self.name, [self], self.type, method, position,
                     state.read, state.set, state.over, state.over_position)

    def __str__(self):
        '''
        Create a string representation of this State.
        '''
        return self.method+"("+"|".join((self.read, self.set, self.over))+")"
    def __repr__(self):
        '''
        Create a string representation of this State.
        '''
        return str(self)
                     
class Tifa(ast.NodeVisitor):
    '''
    '''

    @staticmethod
    def _error_report(error):
        '''
        Return a new unsuccessful report with an error present.
        '''
        return {"success": False, 
                "error": error,
                "issues": {},
                "variables": {}}
    
    @staticmethod
    def _initialize_report():
        '''
        Return a successful report with possible set of issues.
        '''
        return {"success": True,
                "variables": {},
                "issues": {
                    "Parser Failure": [], # Complete failure to parse the code
                    "Unconnected blocks": [], # Any names with ____
                    "Empty Body": [], # Any use of pass on its own
                    "Malformed Conditional": [], # An if/else with empty else or if
                    "Unnecessary Pass": [], # Any use of pass
                    "Unread variables": [], # A variable was not read after it was defined
                    "Undefined variables": [], # A variable was read before it was defined
                    "Possibly undefined variables": [], # A variable was read but was not defined in every branch
                    "Overwritten variables": [], # A written variable was written to again before being read
                    "Append to non-list": [], # Attempted to use the append method on a non-list
                    "Used iteration list": [], # 
                    "Unused iteration variable": [], # 
                    "Non-list iterations": [], # 
                    "Empty iterations": [], # 
                    "Type changes": [], # 
                    "Iteration variable is iteration list": [], # 
                    "Unknown functions": [], # 
                    "Not a function": [], # Attempt to call non-function as function
                    "Recursive Call": [],
                    "Incorrect Arity": [],
                    "Action after return": [],
                    "Incompatible types": [], # 
                    "Return outside function": [], # 
                    "Read out of scope": [], # 
                    "Write out of scope": [], # Attempted to modify a variable in a higher scope
                    "Aliased built-in": [], # 
                    "Method not in Type": [], # A method was used that didn't exist for that type
                    "Submodule not found": [],
                    "Module not found": []
                }
        }
    
    def report_issue(self, issue, data=None):
        '''
        Report the given issue with associated metadata, including the position
        if not explicitly included.
        '''
        if data is None:
            data = {}
        if 'position' not in data:
            data['position'] = self.locate()
        self.report['issues'][issue].append(data)
        
    def locate(self):
        '''
        Return a dictionary representing the current location within the
        AST.
        
        Returns:
            Position dict: A dictionary with the fields 'column' and 'line',
                           indicating the current position in the source code.
        '''
        node = self.node_chain[-1]
        return {'column': node.col_offset, 'line': node.lineno}
                
    def process_code(self, code, filename="__main__"):
        '''
        Processes the AST of the given source code to generate a report.
        
        Args:
            code (str): The Python source code
            filename (str): The filename of the source code (defaults to __main__)
        Returns: 
            Report: The successful or successful report object
        '''
        # Code
        self.source = code.split("\n") if code else []
        filename = filename
        
        # Attempt parsing - might fail!
        try:
            ast_tree = ast.parse(code, filename)
            return self.process_ast(ast_tree)
        except Exception as error:
            self.report = Tifa._error_report(error)
            raise error
            return self.report;
    
    def process_ast(self, ast_tree):
        '''
        Given an AST, actually performs the type and flow analyses to return a 
        report.
        
        Args:
            ast (Ast): The AST object
        Returns:
            Report: The final report object created (also available as a field).
        '''
        self._reset()
        # Initialize a new, empty report
        self.report = Tifa._initialize_report()
        # Traverse every node
        self.visit(ast_tree);
        
        # Check afterwards
        self.report['variables'] = self.name_map
        self._finish_scope()
        
        # Collect top level variables
        self._collect_top_level_varaibles()
        #print(self.report['variables'])
        
        return self.report
    
    def _collect_top_level_varaibles(self):
        '''
        Walk through the variables and add any at the top level to the
        top_level_variables field of the report.
        '''
        self.report['top_level_variables'] = {}
        main_path_vars = self.name_map[self.path_chain[0]]
        for full_name in main_path_vars:
            split_name = full_name.split("/")
            if len(split_name) == 2 and split_name[0] == self.scope_chain[0]:
                self.report.top_level_variables[split_name[1]] = main_path_vars[fullName]
    
    def _reset(self):
        '''
        Reinitialize fields for maintaining the system
        '''
        # Unique Global IDs
        self.path_id = 0;
        self.scope_id = 0;
        self.ast_id = 0;
        
        # Human readable names
        self.path_names = ['*Module'];
        self.scope_names = ['*Module'];
        self.node_chain = [];
        
        # Complete record of all Names
        self.scope_chain = [self.scope_id]
        self.path_chain = [self.path_id]
        self.name_map = {}
        self.name_map[self.path_id] = {}
        self.definition_chain = []
        self.path_parents = {}
        
    def find_variable_scope(self, name):
        '''
        Walk through this scope and all enclosing scopes, finding the relevant
        identifier given by `name`.
        
        Args:
            name (str): The name of the variable
        Returns:
            Identifier: An Identifier for the variable, which could potentially
                        not exist.
        '''
        for scope_index, scope in enumerate(self.scope_chain):
            for path_id in self.path_chain:
                path = self.name_map[path_id]
                full_name = "/".join(map(str, self.scope_chain[:scope_index]))+"/"+name
                if full_name in path:
                    is_root_scope = (scope_index==0)
                    return Identifier(True, is_root_scope, 
                                      full_name, path[full_name])
                        
        return Identifier(False)
    
    def find_variable_out_of_scope(self, name):
        '''
        Walk through every scope and determine if this variable can be found
        elsewhere (which would be an issue).
        
        Args:
            name (str): The name of the variable
        Returns:
            Identifier: An Identifier for the variable, which could potentially
                        not exist.
        '''
        for path in self.name_map.values():
            for full_name in path:
                unscoped_name = full_name.rsplit("/", maxsplit=1)[-1]
                if name == unscoped_name:
                    return Identifier(True, False, unscoped_name, path[full_name])
        return Identifier(False)
        
    def _finish_scope(self):
        '''
        Walk through all the variables present in this scope and ensure that
        they have been read and not overwritten.
        '''
        path_id = self.path_chain[0];
        for name in self.name_map[path_id]:
            if Tifa.in_scope(name, self.scope_chain):
                state = self.name_map[path_id][name]
                if state.over == 'yes':
                    position = state.over_position
                    self.report_issue('Overwritten variables', 
                                     {'name': state.name, 'position': position})
                if state.read == 'no':
                    self.report_issue('Unread variables', 
                                     {'name': state.name, 'type': state.type})
        
    def visit(self, node):
        '''
        Process this node by calling its appropriate visit_*
        
        Args:
            node (AST): The node to visit
        Returns:
            Type: The type calculated during the visit.
        '''
        # Start processing the node
        self.node_chain.append(node)
        self.ast_id += 1
        
        # Actions after return?
        if len(self.scope_chain) > 1:
            return_state = self.find_variable_scope("*return")
            if return_state.exists and return_state.in_scope:
                if return_state.state.set == "yes":
                    self.report_issue("Action after return")
        
        # No? All good, let's enter the node
        result = super().visit(node)
        
        # Pop the node out of the chain
        self.ast_id -= 1
        self.node_chain.pop()
        
        # If a node failed to return something, return the UNKNOWN TYPE
        if result == None:
            return UnknownType()
        else:
            return result
            
    def _visit_nodes(self, nodes):
        '''
        Visit all the nodes in the given list.
        
        Args:
            nodes (list): A list of values, of which any AST nodes will be
                          visited.
        '''
        for node in nodes:
            if isinstance(node, ast.AST):
                self.visit(node)
                
    def walk_targets(self, targets, type, walker):
        '''
        Iterate through the targets and call the given function on each one.
        
        Args:
            targets (list of Ast nodes): A list of potential targets to be
                                         traversed.
            type (Type): The given type to be unraveled and applied to the
                         targets.
            walker (Ast Node, Type -> None): A function that will process
                                             each target and unravel the type.
        '''
        for target in targets:
            walker(target, type)
            
    def visit_Assign(self, node):
        '''
        Simple assignment statement:
        __targets__ = __value__
        
        Args:
            node (AST): An Assign node
        Returns:
            None
        '''
        # Handle value
        value_type = self.visit(node.value);
        # Handle targets
        self._visit_nodes(node.targets);
        
        # TODO: Properly handle assignments with subscripts
        def action(target, type):
            if isinstance(target, ast.Name):
                self.store_variable(target.id, type)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for i, elt in enumerate(target.elts):
                    eltType = type.index(LiteralNum(i))
                    action(elt, eltType)
            elif isinstance(target, ast.Subscript):
                pass
                # TODO: Handle minor type changes (e.g., appending to an inner list)
        self.walk_targets(node.targets, value_type, action)
        
    def visit_AugAssign(self, node):
        # Handle value
        right = self.visit(node.value)
        # Handle target
        left = self.visit(node.target)
        # Target is always a Name, Subscript, or Attribute
        name = self.identify_caller(node.target)
        
        # Handle operation
        self.load_variable(name)
        if isinstance(left, UnknownType) or isinstance(right, UnknownType):
            return UnknownType()
        elif type(node.op) in VALID_BINOP_TYPES:
            op_lookup = VALID_BINOP_TYPES[type(node.op)]
            if type(left) in op_lookup:
                op_lookup = op_lookup[type(left)]
                if type(right) in op_lookup:
                    op_lookup = op_lookup[type(right)]
                    result_type = op_lookup(left, right)
                    self.store_variable(name, result_type)
                    return result_type
        
        self.report_issue("Incompatible types", 
                         {"left": left, "right": right, 
                          "operation": node.op.name})
    
    def visit_BinOp(self, node):
        # Handle left and right
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        # Handle operation
        if isinstance(left, UnknownType) or isinstance(right, UnknownType):
            return UnknownType()
        elif type(node.op) in VALID_BINOP_TYPES:
            op_lookup = VALID_BINOP_TYPES[type(node.op)]
            if type(left) in op_lookup:
                op_lookup = op_lookup[type(left)]
                if type(right) in op_lookup:
                    op_lookup = op_lookup[type(right)]
                    return op_lookup(left, right)
                    
        self.report_issue("Incompatible types", 
                         {"left": left, "right": right, 
                          "operation": node.op.name});
        return UnknownType()
    
    def visit_Import(self, node):
        # Handle names
        for alias in node.names:
            asname = alias.asname or alias.name
            module_type = self.load_module(alias.name)
            self.store_variable(asname, module_type)
            
    def visit_ImportFrom(self, node):
        # Handle names
        for alias in node.names:
            if node.module is None:
                asname = alias.asname or alias.name
                module_type = self.load_module(alias.name)
            else:
                module_name = node.module;
                asname = alias.asname or alias.name
                module_type = self.load_module(module_name)
            name_type = module_type.load_attr(alias.name, self, 
                                              callee_position=self.locate())
            self.store_variable(asname, name_type)
            
    def visit_Name(self, node):
        name = node.id
        if name == "___":
            self.report_issue("Unconnected blocks")
        if isinstance(node.ctx, ast.Load):
            if name == "True" or name == "False":
                return BoolType()
            elif name == "None":
                return NoneType()
            else:
                variable = self.find_variable_scope(name)
                builtin = BUILTINS.get(name)
                if not variable.exists and builtin:
                    return builtin
                else:
                    state = self.load_variable(name)
                    return state.type
        else:
            variable = self.find_variable_scope(name)
            if variable.exists:
                return variable.state.type
            else:
                return UnknownType()
    
    def visit_UnaryOp(self, node):
        # Handle operand
        operand = self.visit(node.operand)
        
        if isinstance(node.op, ast.Not):
            return BoolType()
        elif isinstance(operand, UnknownType):
            return UnknownType()
        elif type(node.op) in VALID_UNARYOP_TYPES:
            op_lookup = VALID_UNARYOP_TYPES[type(node.op)]
            if type(node.op) in op_lookup:
                op_lookup = op_lookup[type(node.op)]
                if type(operand) in op_lookup:
                    op_lookup = op_lookup[type(operand)]
                    return op_lookup(operand)
        return UnknownType()
        
    def _scope_chain_str(self, name=None):
        '''
        Convert the current scope chain to a string representation (divided 
        by "/").
        
        Returns:
            str: String representation of the scope chain.
        '''
        if name:
            return "/".join(map(str, self.scope_chain)) + "/" + name
        else:
            return "/".join(map(str, self.scope_chain))
        
    def identify_caller(self, node):
        '''
        Figures out the variable that was used to kick off this call,
        which is almost always the relevant Name to track as being updated.
        If the origin wasn't a Name, nothing will need to be updated so None
        is returned instead.
        
        TODO: Is this sufficient?
        
        Args:
            node (AST): An AST node
        Returns:
            str or None: The name of the variable or None if no origin could
                         be found.
        '''
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self.identify_caller(node.func)
        elif isinstance(node, (ast.Attribute, ast.Subscript)):
            return self.identify_caller(nodevalue)
        return None
        
    def store_variable(self, name, type):
        '''
        Update the variable with the given name to now have the new type.
        
        Args:
            name (str): The unqualified name of the variable. The variable will
                        be assumed to be in the current scope.
            type (Type): The new type of this variable.
        Returns:
            State: The new state of the variable.
        '''
        full_name = self._scope_chain_str(name)
        current_path = self.path_chain[0]
        variable = self.find_variable_scope(name)
        if not variable.exists:
            # Create a new instance of the variable on the current path
            new_state = State(name, [], type, 'store', self.locate(), 
                              read='no', set='yes', over='no')
            self.name_map[current_path][full_name] = new_state
        else:
            new_state = self.trace_state(variable.state, "store")
            if not variable.in_scope:
                self.report_issue("Write out of scope", {'name': name})
            # Type change?
            if not are_types_equal(type, variable.state.type):
                self.report_issue("Type changes", 
                                 {'name': name, 'old': variable.state.type, 
                                  'new': type})
            new_state.type = type
            # Overwritten?
            if variable.state.set == 'yes' and variable.state.read == 'no':
                new_state.over_position = position
                new_state.over = 'yes'
            else:
                new_state.set = 'yes'
                new_state.read = 'no'
            self.name_map[current_path][full_name] = new_state
        return new_state
    
    def load_variable(self, name):
        '''
        Retrieve the variable with the given name.
        
        Args:
            name (str): The unqualified name of the variable. If the variable is
                        not found in the current scope or an enclosing sope, all
                        other scopes will be searched to see if it was read out
                        of scope.
        Returns:
            State: The current state of the variable.
        '''
        full_name = self._scope_chain_str(name)
        current_path = self.path_chain[0]
        variable = self.find_variable_scope(name)
        if not variable.exists:
            out_of_scope_var = self.find_variable_out_of_scope(name)
            # Create a new instance of the variable on the current path
            if out_of_scope_var.exists:
                self.report_issue("Read out of scope", {'name': name})
            else:
                self.report_issue("Undefined variables", {'name': name})
            new_state = State(name, [], UnknownType(), 'load', self.locate(),
                              read='yes', set='no', over='no')
            self.name_map[current_path][full_name] = new_state
        else:
            new_state = self.trace_state(variable.state, "load")
            if variable.state.set == 'no':
                self.report_issue("Undefined variables", {'name': name})
            if variable.state.set == 'maybe':
                self.report_issue("Possibly undefined variables", {'name': name})
            new_state.read = 'yes';
            if not variable.in_scope:
                self.name_map[current_path][variable.scoped_name] = new_state
            else:
                self.name_map[current_path][full_name] = newState
        return new_state
        
    def load_module(self, chain):
        '''
        Finds the module in the set of available modules.
        
        Args:
            chain (str): A chain of module imports (e.g., "matplotlib.pyplot")
        Returns:
            ModuleType: The specific module with its members, or an empty
                        module type.
        '''
        module_names = chain.split('.')
        if module_names[0] in MODULES:
            base_module = MODULES[module_names[0]]
            for module in module_names:
                if (isinstance(base_module, ModuleType) and 
                    module in base_module.submodules):
                    base_module = base_module.submodules[module]
                else:
                    self.report_issue("Submodule not found", {"name": chain})
            return base_module
        else:
            self.report_issue("Module not found", {"name": chain})
            return ModuleType()
    
    def trace_state(self, state, method):
        '''
        Makes a copy of the given state with the given method type.
        
        Args:
            state (State): The state to copy (as in, we trace a copy of it!)
            method (str): The operation being applied to the state.
        Returns:
            State: The new State
        '''
        return state.copy(method, self.locate())
    
    @staticmethod
    def in_scope(full_name, scope_chain):
        '''
        Determine if the fully qualified variable name is in the given scope
        chain.
        
        Args:
            full_name (str): A fully qualified variable name
            scope_chain (list): A representation of a scope chain.
        Returns:
            bool: Whether the variable lives in this scope
        '''
        # Get this entity's full scope chain
        name_scopes = full_name.split("/")[:-1]
        # against the reverse scope chain
        checking_scopes = scope_chain[::-1]
        return name_scopes == checking_scopes
    