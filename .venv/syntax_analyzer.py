class Token:
    def __init__(self, code, value=None, next_token=None):
        self.code = code  # Token type (e.g., 'ID', 'CT_INT', etc.)
        self.type = code  # Add this line to make it compatible with PLY
        self.value = value
        self.next = next_token


class Parser:
    def __init__(self, tokens):
        self.crtTk = tokens  # Current token
        self.savedTk = None  # For backtracking

    def save(self):
        """Save current token position for backtracking"""
        self.savedTk = self.crtTk

    def restore(self):
        """Restore to previously saved position"""
        if self.savedTk:
            self.crtTk = self.savedTk
            self.savedTk = None

    def consume(self, code):
        print(f"Trying to consume: {code}, Current token: {self.crtTk.code if self.crtTk else 'None'}")
        if self.crtTk and self.crtTk.code == code:
            last_consumed = self.crtTk
            self.crtTk = self.crtTk.next
            return True
        return False

    def unit(self):
        # Iterate through tokens and process declarations/statements
        while self.crtTk and self.crtTk.code != "END":
            # Try each type of declaration/statement with proper backtracking
            startPos = self.crtTk  # Store starting position

            if self.declStruct():
                continue

            self.crtTk = startPos  # Reset position
            if self.declFunc():  # Try function declaration before variable declaration
                continue

            self.crtTk = startPos  # Reset position
            if self.declVar():
                continue

            self.crtTk = startPos  # Reset position
            if self.stm():
                continue

            # If we get here, no valid parsing function succeeded
            raise SyntaxError(f"Unexpected token: {self.crtTk.code if self.crtTk else 'None'}")

        # Consume the END token if present
        if self.crtTk and self.crtTk.code == "END":
            self.consume("END")

        return True

    def declStruct(self):
        print("Checking declStruct")
        if not self.consume("STRUCT"):
            return False
        if not self.consume("ID"):
            raise SyntaxError("Expected ID after STRUCT")

        # This is the key difference - we check for LACC to determine if it's a struct definition
        if not self.consume("LACC"):
            # This isn't a struct definition but possibly a variable declaration
            # We'll let declVar handle this by backtracking
            return False

        while self.declVar():
            pass
        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close struct definition")
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after struct definition")
        return True

    def declVar(self):
        print("Checking declVar")
        startPos = self.crtTk  # Store position for backtracking

        if not self.typeBase():
            self.crtTk = startPos  # Restore position
            return False

        # Process first variable
        if not self.consume("ID"):
            self.crtTk = startPos  # Restore position
            return False

        self.arrayDecl()  # This is optional, so no need to check return value

        # Process additional variables separated by commas
        while self.consume("COMMA"):
            if not self.consume("ID"):
                raise SyntaxError("Expected variable name after comma")
            self.arrayDecl()

        # Require semicolon at end
        if not self.consume("SEMICOLON"):
            self.crtTk = startPos  # Restore position if no semicolon
            return False

        return True

    def typeBase(self):
        print("Checking typeBase")
        startPos = self.crtTk  # Store for backtracking

        if self.consume("INT"):
            print("Found INT")
            return True
        if self.consume("DOUBLE"):
            print("Found DOUBLE")
            return True
        if self.consume("CHAR"):
            print("Found CHAR")
            return True
        if self.consume("VOID"):
            print("Found VOID")
            return True

        # Reset position for struct check
        self.crtTk = startPos
        if self.consume("STRUCT") and self.consume("ID"):
            print("Found STRUCT ID")
            return True

        self.crtTk = startPos  # Restore position on failure
        print("typeBase failed")
        return False

    def arrayDecl(self):
        if not self.consume("LBRACKET"):
            return False
        if not self.expr():
            raise SyntaxError("Expected expression in array declaration")
        if not self.consume("RBRACKET"):
            raise SyntaxError("Expected ] in array declaration")
        return True

    def declFunc(self):
        print("Checking declFunc")
        startPos = self.crtTk  # Store for backtracking

        # Return type: either a type or void
        if not self.typeBase():
            self.crtTk = startPos
            return False

        # Function name
        if not self.consume("ID"):
            self.crtTk = startPos
            return False

        # Function parameters
        if not self.consume("LPAR"):
            self.crtTk = startPos
            return False

        # Handle parameters - first parameter
        if self.funcArg():
            # Additional parameters
            while self.consume("COMMA"):
                if not self.funcArg():
                    raise SyntaxError("Expected function argument after comma")

        # Close parameters
        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) to close function parameters")

        # Function body
        if not self.stmCompound():
            raise SyntaxError("Expected function body { ... }")

        return True

    def funcArg(self):
        startPos = self.crtTk  # Store for backtracking

        # Parameter type
        if not self.typeBase():
            self.crtTk = startPos
            return False

        # Parameter name
        if not self.consume("ID"):
            self.crtTk = startPos
            return False

        # Optional array brackets
        self.arrayDecl()  # This is optional

        return True

    def stm(self):
        startPos = self.crtTk  # Store for backtracking

        # Try each statement type
        if self.stmCompound():
            return True

        self.crtTk = startPos
        if self.stmIf():
            return True

        self.crtTk = startPos
        if self.stmWhile():
            return True

        self.crtTk = startPos
        if self.stmFor():
            return True

        self.crtTk = startPos
        if self.stmBreak():
            return True

        self.crtTk = startPos
        if self.stmReturn():
            return True

        self.crtTk = startPos
        if self.stmAssign():
            return True

        self.crtTk = startPos
        if self.stmExpr():
            return True

        return False

    def stmCompound(self):
        if not self.consume("LACC"):
            return False

        # Process declarations and statements inside the block
        while True:
            startPos = self.crtTk

            if self.declVar():
                continue

            self.crtTk = startPos
            if self.stm():
                continue

            break  # No more declarations or statements

        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close compound statement")

        return True

    def expr(self):
        startPos = self.crtTk
        if self.exprAssign():
            return True
        self.crtTk = startPos
        return False

    def stmExpr(self):
        startPos = self.crtTk
        if not self.expr():
            return False
        if not self.consume("SEMICOLON"):
            self.crtTk = startPos
            return False
        return True

    def exprAssign(self):
        startPos = self.crtTk

        # Check for a variable or other lvalue
        if not self.exprOr():
            return False

        # If followed by assignment, it's an assignment expression
        if self.consume("ASSIGN"):
            if not self.exprAssign():
                raise SyntaxError("Expected expression after =")
            return True

        # Otherwise, it's just a regular or expression
        return True

    def exprOr(self):
        if not self.exprAnd():
            return False
        while self.consume("OR"):
            if not self.exprAnd():
                raise SyntaxError("Expected expression after OR")
        return True

    def exprAnd(self):
        if not self.exprEq():
            return False
        while self.consume("AND"):
            if not self.exprEq():
                raise SyntaxError("Expected expression after AND")
        return True

    def exprEq(self):
        if not self.exprRel():
            return False
        while self.consume("EQUAL") or self.consume("NOTEQ"):
            if not self.exprRel():
                raise SyntaxError("Expected expression after equality operator")
        return True

    def exprRel(self):
        if not self.exprAdd():
            return False
        while self.consume("LESS") or self.consume("LESSEQ") or \
                self.consume("GREATER") or self.consume("GREATEREQ"):
            if not self.exprAdd():
                raise SyntaxError("Expected expression after relational operator")
        return True

    def exprAdd(self):
        if not self.exprMul():
            return False
        while self.consume("ADD") or self.consume("SUB"):
            if not self.exprMul():
                raise SyntaxError("Expected expression after additive operator")
        return True

    def exprMul(self):
        if not self.exprCast():
            return False
        while self.consume("MUL") or self.consume("DIV"):
            if not self.exprCast():
                raise SyntaxError("Expected expression after multiplicative operator")
        return True

    def exprCast(self):
        return self.exprUnary()

    def exprUnary(self):
        if self.consume("SUB") or self.consume("NOT"):
            return self.exprUnary()
        return self.exprPrimary()

    def exprPrimary(self):
        # Check for ID - variable, function call, or array reference
        if self.consume("ID"):
            # Array access
            while self.consume("LBRACKET"):
                if not self.expr():
                    raise SyntaxError("Expected expression inside [ ]")
                if not self.consume("RBRACKET"):
                    raise SyntaxError("Expected ] after array index")

            # Struct member access
            while self.consume("DOT"):
                if not self.consume("ID"):
                    raise SyntaxError("Expected field name after .")

            # Function call
            if self.consume("LPAR"):
                # Handle arguments
                if self.expr():
                    while self.consume("COMMA"):
                        if not self.expr():
                            raise SyntaxError("Expected expression after comma")
                if not self.consume("RPAR"):
                    raise SyntaxError("Expected ) in function call")
            return True

        # Check for constants
        if self.consume("CT_INT") or self.consume("CT_REAL") or self.consume("CT_CHAR") or self.consume("CT_STRING"):
            return True

        # Check for parenthesized expression
        if self.consume("LPAR"):
            if not self.expr():
                raise SyntaxError("Expected expression after (")
            if not self.consume("RPAR"):
                raise SyntaxError("Expected )")
            return True

        return False

    def stmAssign(self):
        startPos = self.crtTk

        # First token must be an ID
        if not self.consume("ID"):
            return False

        # Array access
        while self.consume("LBRACKET"):
            if not self.expr():
                raise SyntaxError("Expected expression inside [ ]")
            if not self.consume("RBRACKET"):
                raise SyntaxError("Expected ] after array index")

        # Struct member access
        while self.consume("DOT"):
            if not self.consume("ID"):
                raise SyntaxError("Expected field name after .")

        # Must have assignment operator
        if not self.consume("ASSIGN"):
            self.crtTk = startPos
            return False

        # Must have expression after assignment
        if not self.expr():
            raise SyntaxError("Expected expression after =")

        # Must end with semicolon
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after assignment statement")

        return True

    def stmIf(self):
        if not self.consume("IF"):
            return False
        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( after if")
        if not self.expr():
            raise SyntaxError("Expected condition in if statement")
        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) after if condition")
        if not self.stm():
            raise SyntaxError("Expected statement for if block")
        if self.consume("ELSE"):
            if not self.stm():
                raise SyntaxError("Expected statement for else block")
        return True

    def stmWhile(self):
        if not self.consume("WHILE"):
            return False
        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( after while")
        if not self.expr():
            raise SyntaxError("Expected condition in while statement")
        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) after while condition")
        if not self.stm():
            raise SyntaxError("Expected statement for while block")
        return True

    def stmFor(self):
        if not self.consume("FOR"):
            return False
        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( after for")

        # Expression 1 (initialization) - optional
        self.expr()  # We don't check the return since it's optional
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after for initialization")

        # Expression 2 (condition) - optional
        self.expr()  # Optional
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after for condition")

        # Expression 3 (increment) - optional
        self.expr()  # Optional
        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) after for loop")

        if not self.stm():
            raise SyntaxError("Expected statement for for block")
        return True

    def stmBreak(self):
        if not self.consume("BREAK"):
            return False
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after break")
        return True

    def stmReturn(self):
        if not self.consume("RETURN"):
            return False

        # Return value is optional
        self.expr()  # We don't check the return value

        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after return")
        return True