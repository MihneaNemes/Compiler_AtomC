import os
from lexical_analyzer import lexer
from syntax_analyzer import Token  # Import your custom Token class


def test_lexer_file(file_path):
    """Test lexer with input from a file"""
    with open(file_path, 'r') as f:
        code = f.read()

    print(f"\n=== Testing file: {os.path.basename(file_path)} ===")
    print("Input code:\n" + "=" * 40)
    print(code.strip())
    print("=" * 40 + "\nTokens:")

    lexer.input(code)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        # Convert LexToken to your custom Token class
        custom_token = Token(code=tok.type, value=tok.value)
        tokens.append((custom_token.code, custom_token.value))
        print(f"{custom_token.code:10} -> {custom_token.value}")

    print("\nToken summary:")
    for i, (token_type, value) in enumerate(tokens, 1):
        print(f"{i:3}. {token_type:15} {str(value):20}")

    return tokens


if __name__ == "__main__":
    test_file = r"tests\8.c"  # Your test file
    if os.path.exists(test_file):
        test_lexer_file(test_file)
    else:
        print(f"Error: File not found - {test_file}")
