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
        if self.crtTk and self.crtTk.code == code:
            self.crtTk = self.crtTk.next
            return True
        return False

    def unit(self):
        while self.declStruct() or self.declFunc() or self.declVar():
            pass
        return self.consume("END")

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
        while self.consume("COMMA"):
            if not self.consume("ID"):
                raise SyntaxError("Expected variable name after comma")
            self.arrayDecl()
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after variable declaration")
        return True

    def typeBase(self):
        return self.consume("INT") or self.consume("DOUBLE") or self.consume("CHAR") or (self.consume("STRUCT") and self.consume("ID"))

    def arrayDecl(self):
        if not self.consume("LBRACKET"):
            return False
        self.expr()
        if not self.consume("RBRACKET"):
            raise SyntaxError("Expected ] in array declaration")
        return True

    def declFunc(self):
        if not (self.typeBase() and self.consume("MUL")) and not self.consume("VOID"):
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
        return self.stmCompound() or self.stmIf() or self.stmWhile() or self.stmFor() or self.stmBreak() or self.stmReturn() or self.expr()

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
        if self.exprUnary() and self.consume("ASSIGN"):
            if not self.exprAssign():
                raise SyntaxError("Expected expression after =")
            return True
        return self.exprOr()

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
                raise SyntaxError("Expected expression after comparison operator")
        return True

    def exprRel(self):
        if not self.exprAdd():
            return False
        while self.consume("LESS") or self.consume("LESSEQ") or self.consume("GREATER") or self.consume("GREATEREQ"):
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
        if self.consume("LPAR"):
            if not self.typeName():
                raise SyntaxError("Expected type in cast expression")
            if not self.consume("RPAR"):
                raise SyntaxError("Expected ) after cast")
            return self.exprCast()
        return self.exprUnary()

    def exprUnary(self):
        if self.consume("SUB") or self.consume("NOT"):
            return self.exprUnary()
        return self.exprPrimary()

    def exprPrimary(self):
        if self.consume("ID"):
            if self.consume("LPAR"):
                if self.expr():
                    while self.consume("COMMA"):
                        if not self.expr():
                            raise SyntaxError("Expected expression after comma in function call")
                if not self.consume("RPAR"):
                    raise SyntaxError("Expected ) in function call")
            return True
        return self.consume("CT_INT") or self.consume("CT_REAL") or self.consume("CT_CHAR") or self.consume("CT_STRING") or (self.consume("LPAR") and self.expr() and self.consume("RPAR"))
#