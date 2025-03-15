from lexical_analyzer import lexer
from syntax_analyzer import Parser, Token

# Test data
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

# Tokenize input
lexer.input(data)

# Collect tokens into a list
tokens = []
while True:
    tok = lexer.token()
    if not tok:
        break
    # Convert LexToken to Token
    token = Token(code=tok.type, value=tok.value)
    tokens.append(token)

# Convert list to linked list
for i in range(len(tokens) - 1):
    tokens[i].next = tokens[i + 1]

# Create parser and parse the token stream
parser = Parser(tokens[0])
if parser.unit():  # Call the `unit` method instead of `parse`
    print("Parsing successful!")
else:
    print("Parsing failed!")