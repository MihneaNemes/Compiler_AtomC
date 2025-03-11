# main.py
from lexical_analyzer import lexer

# Test data
data = """
int main() {
    int a =                   10;
    double b =               3.14;
    double c = 3.m14;  // Invalid number
    char d = 'x';
    char *str = "Hello, World!";
    if (a < b) {
        return 0;
    }
}
"""

# Input the data into the lexer
lexer.input(data)

# Tokenize and print tokens
while True:
    tok = lexer.token()
    if not tok:
        break  # No more input
    if tok.type == 'INVALID':
        print(f"Invalid token: {tok.value}")
    else:
        print(tok)