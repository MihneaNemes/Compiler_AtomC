class Token:
    def __init__(self, code, value=None, next_token=None):
        self.code = code  # Token type (e.g., 'ID', 'CT_INT', etc.)
        self.type = code  # Add this line to make it compatible with PLY
        self.value = value
        self.next = next_token

class Parser:
    def __init__(self, tokens):
        self.crtTk = tokens  # Current token

    def consume(self, code):
        print(f"Trying to consume: {code}, Current token: {self.crtTk.code if self.crtTk else 'None'}")
        if self.crtTk and self.crtTk.code == code:
            last_consumed = self.crtTk
            self.crtTk = self.crtTk.next
            return True
        return False

    def unit(self):
        # Parse declarations (struct, function, variable)
        while self.declStruct() or self.declFunc() or self.declVar() or self.stm():
            pass

        # Consume the END token
        if not self.consume("END"):
            raise SyntaxError("Expected END token at the end of input")
        return True

    def declStruct(self):
        if not self.consume("STRUCT"):
            return False
        if not self.consume("ID"):
            raise SyntaxError("Expected ID after STRUCT")
        if not self.consume("LACC"):
            raise SyntaxError("Expected { after STRUCT ID")
        while self.declVar():
            pass
        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close struct definition")
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after struct definition")
        return True

    def declVar(self):
        if not self.typeBase():
            return False
        if not self.consume("ID"):
            raise SyntaxError("Expected variable name")
        self.arrayDecl()
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after variable declaration")
        return True

    def typeBase(self):
        print("Checking typeBase")
        if self.consume("INT"):
            print("Found INT")
            return True
        if self.consume("DOUBLE"):
            print("Found DOUBLE")
            return True
        if self.consume("CHAR"):
            print("Found CHAR")
            return True
        if self.consume("STRUCT") and self.consume("ID"):
            print("Found STRUCT ID")
            return True
        print("typeBase failed")
        return False

    def arrayDecl(self):
        if not self.consume("LBRACKET"):
            return False
        self.expr()
        if not self.consume("RBRACKET"):
            raise SyntaxError("Expected ] in array declaration")
        return True

    def declFunc(self):
        if not (self.typeBase() and not self.consume("VOID")):
            return False
        if not self.consume("ID"):
            raise SyntaxError("Expected function name")
        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( in function declaration")
        if self.funcArg():
            while self.consume("COMMA"):
                if not self.funcArg():
                    raise SyntaxError("Expected function argument after comma")
        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) to close function parameters")
        if not self.stmCompound():
            raise SyntaxError("Expected function body")
        return True

    def funcArg(self):
        if not self.typeBase():
            return False
        if not self.consume("ID"):
            raise SyntaxError("Expected argument name")
        self.arrayDecl()
        return True

    def stm(self):
        return self.stmAssign() or self.stmCompound() or self.stmIf() or self.stmWhile() or self.stmFor() or self.stmBreak() or self.stmReturn() or self.expr()

    def stmCompound(self):
        if not self.consume("LACC"):
            return False
        while self.declVar() or self.stm():
            pass
        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close compound statement")
        return True

    def expr(self):
        return self.exprAssign()

    def exprAssign(self):
        # Handle assignment expressions (lowest precedence)
        if self.exprOr():
            if self.consume("ASSIGN"):
                return self.exprAssign()
            return True
        return False

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
        # Handle type casts if needed (e.g., (int)x)
        return self.exprUnary()

    def exprUnary(self):
        # Handle unary operators (-, !)
        if self.consume("SUB") or self.consume("NOT"):
            return self.exprUnary()
        return self.exprPrimary()

    def exprPrimary(self):
        # Handle identifiers, constants, and parentheses
        if self.consume("ID"):
            # Check for function calls (e.g., foo(...))
            if self.consume("LPAR"):
                if self.expr():
                    while self.consume("COMMA"):
                        if not self.expr():
                            raise SyntaxError("Expected expression after comma")
                if not self.consume("RPAR"):
                    raise SyntaxError("Expected ) in function call")
            return True
        return (
                self.consume("CT_INT") or
                self.consume("CT_REAL") or
                self.consume("CT_CHAR") or
                self.consume("CT_STRING") or
                (self.consume("LPAR") and self.expr() and self.consume("RPAR"))
        )

    def stmAssign(self):
        if not self.consume("ID"):  # Expect an identifier
            return False
        if not self.consume("ASSIGN"):  # Expect an '=' symbol
            return False
        if not self.expr():  # Expect an expression after '='
            raise SyntaxError("Expected expression after =")
        if not self.consume("SEMICOLON"):  # Expect ';' at the end
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
        if not self.expr():
            raise SyntaxError("Expected initialization in for loop")
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after for initialization")
        if not self.expr():
            raise SyntaxError("Expected condition in for loop")
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after for condition")
        if not self.expr():
            raise SyntaxError("Expected increment in for loop")
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
        if self.expr():  # Optional return value
            pass
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after return")
        return True