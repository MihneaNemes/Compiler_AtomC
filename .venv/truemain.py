import os
import traceback
from contextlib import redirect_stdout
from lexical_analyzer import lexer
from syntax_analyzer import Parser, Token


def read_input_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


# Configuration paths
folder_path = r'C:\Users\mihne\OneDrive\Desktop\sarpili\Compiler_AtomC\.venv\tests'
output_file_path = r'C:\Users\mihne\OneDrive\Desktop\sarpili\Compiler_AtomC\.venv\output.txt'

with open(output_file_path, 'w') as output_file:
    with redirect_stdout(output_file):
        print("===== Compiler Analysis Results =====")

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if not os.path.isfile(file_path):
                continue

            try:
                print(f"\nProcessing file: {filename}")

                # Read and tokenize input
                data = read_input_from_file(file_path)
                lexer.input(data)

                # Convert to custom Token objects
                tokens = []
                while True:
                    tok = lexer.token()
                    if not tok:
                        tokens.append(Token(code='END', value='None'))
                        break
                    tokens.append(Token(code=tok.type, value=tok.value))

                # Link tokens as a linked list
                for i in range(len(tokens) - 1):
                    tokens[i].next = tokens[i + 1]

                # Parse tokens
                parser = Parser(tokens[0])
                result = parser.unit()

                print(f"Result for {filename}: {'SUCCESS ✅' if result else 'FAILURE ❌'}")

            except Exception as e:
                print(f"\n⚠️ Error processing {filename}:")
                traceback.print_exc()
                print("=" * 50)

        print("\n===== Analysis Complete =====")