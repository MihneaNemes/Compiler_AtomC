import os
from lexical_analyzer import lexer
from syntax_analyzer import Parser, Token


def read_input_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


# Folder path containing your test files
folder_path = r'C:\Users\mihne\OneDrive\Desktop\sarpili\Compiler_AtomC\.venv\tests'  # Update this path

# Iterate over each file in the folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Skip directories, process only files
    if os.path.isfile(file_path):
        print(f"\nProcessing file: {filename}")

        # Read input from the current file
        data = read_input_from_file(file_path)

        # Tokenize input
        lexer.input(data)
        tokens = []
        while True:
            tok = lexer.token()
            if not tok:
                # Add END token
                token = Token(code='END', value='None')
                tokens.append(token)
                break
            # Convert LexToken to your custom Token
            token = Token(code=tok.type, value=tok.value)
            tokens.append(token)

        # Link tokens into a linked list
        for i in range(len(tokens) - 1):
            tokens[i].next = tokens[i + 1]

        # Create parser and parse
        parser = Parser(tokens[0])
        if parser.unit():
            print(f"✅ {filename}: Parsing successful!")
        else:
            print(f"❌ {filename}: Parsing failed!")