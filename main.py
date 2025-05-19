from lexical_analyzer import lexer
from syntax_analyzer import Parser, Token
from syntax_analyzer import SemanticError

# Function to read input from a file
def read_input_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# File path to the input file
input_file_path = r'C:\Users\mihne\OneDrive\Desktop\sarpili\Compiler_AtomC\input'

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

# Debug Step 1: Print the token stream to verify lexer output
print("Token Stream:")
current = tokens[0]
while current:
    print(f"  {current.code}('{current.value}')")
    current = current.next
print("End of Token Stream\n")

# Create parser and parse the token stream
parser = Parser(tokens[0])

# Debug Step 2: Modify the consume method to trace token consumption
original_consume = parser.consume

def debug_consume(code):
    print(f"Trying to consume: {code}, Current token: {parser.crtTk.code if parser.crtTk else 'None'}")
    result = original_consume(code)
    if result:
        print(f"Consumed: {result.code}('{result.value}')")
    return result

parser.consume = debug_consume

# Parse and handle exceptions
try:
    result = parser.unit()
    print("SUCCESS")
except SyntaxError as e:
    print(f"Syntax error: {e}")
except SemanticError as e:
    print(f"Semantic error: {e}")
    # Debug Step 3: Print context around the error
    if parser.crtTk:
        print(f"Error occurred at token: {parser.crtTk.code}('{parser.crtTk.value}')")
        if parser.crtTk.next:
            print(f"Next token: {parser.crtTk.next.code}('{parser.crtTk.next.value}')")
        if parser.crtTk.next and parser.crtTk.next.next:
            print(f"Following token: {parser.crtTk.next.next.code}('{parser.crtTk.next.next.value}')")