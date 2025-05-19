import ply.lex as lex

from syntax_analyzer import Token

tokens = [
    'ID', 'CT_INT', 'CT_REAL', 'CT_CHAR', 'CT_STRING',
    'COMMA', 'SEMICOLON', 'LPAR', 'RPAR', 'LBRACKET', 'RBRACKET', 'LACC', 'RACC',
    'ADD', 'SUB', 'MUL', 'DIV', 'DOT', 'AND', 'OR', 'NOT', 'ASSIGN', 'EQUAL', 'NOTEQ', 'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ',
    'BREAK', 'CHAR', 'DOUBLE', 'ELSE', 'FOR', 'IF', 'INT', 'RETURN', 'STRUCT', 'VOID', 'WHILE', 'INVALID', 'END'
]

t_COMMA = r','
t_SEMICOLON = r';'
t_LPAR = r'\('
t_RPAR = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LACC = r'\{'
t_RACC = r'\}'
t_ADD = r'\+'
t_SUB = r'-'
t_MUL = r'\*'
t_DIV = r'/'
t_DOT = r'\.'
t_AND = r'&&'
t_OR = r'\|\|'
t_NOT = r'!'
t_ASSIGN = r'='
t_EQUAL = r'=='
t_NOTEQ = r'!='
t_LESS = r'<'
t_LESSEQ = r'<='
t_GREATER = r'>'
t_GREATEREQ = r'>='

keywords = {
    'break': 'BREAK',
    'char': 'CHAR',
    'double': 'DOUBLE',
    'else': 'ELSE',
    'for': 'FOR',
    'if': 'IF',
    'int': 'INT',
    'return': 'RETURN',
    'struct': 'STRUCT',
    'void': 'VOID',
    'while': 'WHILE'
}

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value, 'ID')
    return Token(code=t.type, value=t.value)

def t_CT_HEX(t):
    r'0[xX][0-9a-fA-F]+'
    t.value = int(t.value, 16)
    return Token(code='CT_INT', value=t.value)

def t_CT_OCTAL(t):
    r'0[0-7]+'
    t.value = int(t.value, 8)
    return Token(code='CT_INT', value=t.value)

def t_CT_REAL(t):
    r'((\d+\.\d*([eE][+-]?\d+)?)|(\.\d+([eE][+-]?\d+)?)|(\d+[eE][+-]?\d+))'
    try:
        t.value = float(t.value)
    except ValueError:
        print(f"Invalid real number: {t.value}")
        return Token(code='INVALID', value=t.value)
    return Token(code='CT_REAL', value=t.value)

def t_CT_INT_DECIMAL(t):
    r'[1-9]\d*|0'
    t.value = int(t.value)
    return Token(code='CT_INT', value=t.value)

def t_CT_CHAR(t):
    r"'([^'\\]|\\.)'"
    return Token(code='CT_CHAR', value=t.value)

def t_CT_STRING(t):
    r'"([^"\\]|\\.)*"'
    return Token(code='CT_STRING', value=t.value)

def t_COMMENT(t):
    r'//.*|\/\*(.|\n)*?\*\/'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_END(t):
    r'\0'
    return Token(code='END', value=None)

t_ignore = ' \t\r'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()