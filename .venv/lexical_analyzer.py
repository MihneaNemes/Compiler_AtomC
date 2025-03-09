import ply.lex as lex

# List of token names
tokens = [
    'ID', 'CT_INT', 'CT_REAL', 'CT_CHAR', 'CT_STRING',
    'COMMA', 'SEMICOLON', 'LPAR', 'RPAR', 'LBRACKET', 'RBRACKET', 'LACC', 'RACC',
    'ADD', 'SUB', 'MUL', 'DIV', 'DOT', 'AND', 'OR', 'NOT', 'ASSIGN', 'EQUAL', 'NOTEQ', 'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ',
    'BREAK', 'CHAR', 'DOUBLE', 'ELSE', 'FOR', 'IF', 'INT', 'RETURN', 'STRUCT', 'VOID', 'WHILE', 'INVALID'
]

# Regular expression rules for simple tokens
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

# Regular expression rules with actions
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Check if the identifier is a keyword
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
    t.type = keywords.get(t.value, 'ID')  # Assign the token type
    return t

def t_CT_CHAR(t):
    r"'([^'\\]|\\.)'"
    return t

def t_CT_STRING(t):
    r'"([^"\\]|\\.)*"'
    return t

# FSM Lexer for integers, real numbers, and comments
def t_CT_INT_or_REAL_or_COMMENT(t):
    r'\d+(\.\d+)?(e[+-]?\d+)?|\{.*?\}'
    input_string = t.value
    pCrtCh = 0
    state = 0
    i = 0
    r = 0.0
    fp = 0.0

    while True:
        if pCrtCh >= len(input_string):
            ch = '\0'  # End of input
        else:
            ch = input_string[pCrtCh]

        if state == 0:  # Initial state
            if ch.isdigit():
                i = int(ch)
                pCrtCh += 1
                state = 1
            elif ch == '{':
                pCrtCh += 1
                state = 6
            elif ch == '\0':
                t.type = 'END'
                return t
            else:
                t.type = 'INVALID'
                return t

        elif state == 1:  # Reading integer part
            if ch.isdigit():
                i = i * 10 + int(ch)
                pCrtCh += 1
            elif ch == '.':
                pCrtCh += 1
                state = 2
            else:
                state = 5

        elif state == 2:  # After decimal point, expecting a digit
            if ch.isdigit():
                fp = 0.1
                r = i + int(ch) * fp
                pCrtCh += 1
                state = 3
            else:
                # Invalid number (e.g., "3.m14")
                t.type = 'INVALID'
                return t

        elif state == 3:  # Reading fractional part
            if ch.isdigit():
                fp /= 10
                r += int(ch) * fp
                pCrtCh += 1
            else:
                state = 4

        elif state == 4:  # End of real number
            t.type = 'CT_REAL'
            t.value = r
            return t

        elif state == 5:  # End of integer
            t.type = 'CT_INT'
            t.value = i
            return t

        elif state == 6:  # Inside a comment block
            if ch == '}':
                pCrtCh += 1
                state = 0
            elif ch == '\0':
                t.type = 'INVALID'
                return t
            else:
                pCrtCh += 1

# Ignored characters (spaces, tabs, newlines)
t_ignore = ' \t\n\r'

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Test the lexer
data = """
int main() {
    int a = 10;
    double b = 3.14;
    double c = 3.m14;  // Invalid number
    char d = 'x';
    char *str = "Hello, World!";
    if (a < b) {
        return 0;
    }
}
"""

lexer.input(data)

# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break  # No more input
    if tok.type == 'INVALID':
        print(f"Invalid token: {tok.value}")
    else:
        print(tok)