from lexical_analyzer import lexer
from syntax_analyzer import Parser, Token

# Function to read input from a file
def read_input_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# File path to the input file
input_file_path = r'C:\Users\mihne\OneDrive\Desktop\sarpili\Compiler_AtomC\.venv\input'

# Read input from the file
data = read_input_from_file(input_file_path)

# Tokenize input
lexer.input(data)

# Collect tokens into a list
tokens = []
while True:
    tok = lexer.token()
    if not tok:
        token = Token(code='END', value='None')
        tokens.append(token)
        break
    # Convert LexToken to Token
    token = Token(code=tok.type, value=tok.value)
    tokens.append(token)

# Convert list to linked list
for i in range(len(tokens) - 1):
    tokens[i].next = tokens[i + 1]

# Create parser and parse the token stream
parser = Parser(tokens[0])
try:
    result = parser.unit()
    print(f"Result for {filename}: {'SUCCESS' if result else 'FAILURE'}")
except SyntaxError as e:
    print(f"Syntax error: {e}")
except SemanticError as e:
    print(f"Semantic error: {e}")