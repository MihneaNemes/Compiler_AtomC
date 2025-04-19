class Token:
    def __init__(self, code, value=None, next_token=None, text=None):
        self.code = code  # Token type (e.g., 'ID', 'CT_INT', etc.)
        self.type = code  # Add this line to make it compatible with PLY
        self.value = value
        self.text = text if text is not None else value  # Store the token text
        self.next = next_token


class Type:
    def __init__(self):
        self.typeBase = None  # TB_INT, TB_DOUBLE, TB_CHAR, TB_VOID, TB_STRUCT
        self.nElements = -1  # -1 for non-array, 0 for arrays with unknown size, >0 for arrays with known size
        self.s = None  # Symbol reference for struct types


class Symbol:
    def __init__(self, name, cls):
        self.name = name  # Symbol name
        self.cls = cls  # CLS_VAR, CLS_FUNC, CLS_STRUCT
        self.depth = 0  # Symbol scope depth
        self.mem = None  # MEM_GLOBAL, MEM_LOCAL, MEM_ARG`
        self.type = Type()  # Symbol type
        self.args = None  # For functions: list of argument symbols
        self.members = None  # For structs: list of member symbols


class SymbolTable:
    def __init__(self):
        self.begin = []  # List of symbols
        self.end = []  # End marker for each depth level

    def init_symbols(self):
        self.begin = []
        self.end = [None]  # Initial end marker


def find_symbol(symtab, name):
    """Find a symbol in the symbol table by name"""
    for s in reversed(symtab.begin):
        if s.name == name:
            return s
    return None


def add_symbol(symtab, name, cls):
    """Add a symbol to the symbol table"""
    s = Symbol(name, cls)
    s.depth = crtDepth
    symtab.begin.append(s)
    return s


def delete_symbols_after(symtab, start):
    """Delete all symbols after the given symbol"""
    if start is None:
        # Delete all symbols from the current depth
        symtab.begin = [s for s in symtab.begin if s.depth < crtDepth]
    else:
        # Find the index of the start symbol
        try:
            idx = symtab.begin.index(start)
            # Keep symbols up to and including start
            symtab.begin = symtab.begin[:idx + 1]
        except ValueError:
            # Symbol not found, don't delete anything
            pass


# Global variables for semantic analysis
symbols = SymbolTable()
crtDepth = 0
crtFunc = None
crtStruct = None


def init_globals():
    global symbols, crtDepth, crtFunc, crtStruct
    symbols = SymbolTable()
    symbols.init_symbols()
    crtDepth = 0
    crtFunc = None
    crtStruct = None


def tkerr(tk, msg, *args):
    """Report a semantic error"""
    formatted_msg = msg % args if args else msg
    line_info = f" at line {tk.line}" if hasattr(tk, 'line') else ""
    raise SemanticError(f"{formatted_msg}{line_info}")


class SemanticError(Exception):
    """Exception for semantic errors"""
    pass


class Parser:
    def __init__(self, tokens):
        self.crtTk = tokens  # Current token
        init_globals()  # Initialize semantic analysis globals

    def save(self):
        """Save current token position for backtracking"""
        return self.crtTk

    def restore(self, saved_pos):
        """Restore to previously saved position"""
        self.crtTk = saved_pos

    def consume(self, code):
        print(f"Trying to consume: {code}, Current token: {self.crtTk.code if self.crtTk else 'None'}")
        if self.crtTk and self.crtTk.code == code:
            last_consumed = self.crtTk
            self.crtTk = self.crtTk.next
            return last_consumed  # Return the consumed token
        return None

    def unit(self):
        # Iterate through tokens and process declarations/statements
        while self.crtTk and self.crtTk.code != "END":
            # Try each type of declaration/statement with proper backtracking
            startPos = self.save()

            if self.declStruct():
                continue

            self.restore(startPos)
            if self.declFunc():
                continue

            self.restore(startPos)
            if self.declVar():
                continue

            self.restore(startPos)
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

        # Get struct name token
        tkName = self.consume("ID")
        if not tkName:
            raise SyntaxError("Expected ID after STRUCT")

        if not self.consume("LACC"):
            # Not a struct definition
            return False

        # Semantic action: Check for symbol redefinition and create struct symbol
        global crtStruct
        if find_symbol(symbols, tkName.text):
            tkerr(self.crtTk, "symbol redefinition: %s", tkName.text)
        crtStruct = add_symbol(symbols, tkName.text, "CLS_STRUCT")
        crtStruct.members = SymbolTable()
        crtStruct.members.init_symbols()

        # Process struct members
        while self.declVar():
            pass

        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close struct definition")
        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after struct definition")

        # Clear current struct pointer
        crtStruct = None
        return True

    def add_var(self, tkName, t):
        """Helper function to add variables with semantic analysis"""
        global crtStruct, crtFunc, crtDepth

        s = None
        if crtStruct:
            if find_symbol(crtStruct.members, tkName.text):
                tkerr(self.crtTk, "symbol redefinition: %s", tkName.text)
            s = add_symbol(crtStruct.members, tkName.text, "CLS_VAR")
        elif crtFunc:
            s = find_symbol(symbols, tkName.text)
            if s and s.depth == crtDepth:
                tkerr(self.crtTk, "symbol redefinition: %s", tkName.text)
            s = add_symbol(symbols, tkName.text, "CLS_VAR")
            s.mem = "MEM_LOCAL"
        else:
            if find_symbol(symbols, tkName.text):
                tkerr(self.crtTk, "symbol redefinition: %s", tkName.text)
            s = add_symbol(symbols, tkName.text, "CLS_VAR")
            s.mem = "MEM_GLOBAL"

        s.type = t
        return s

    def declVar(self):
        print("Checking declVar")
        startPos = self.save()

        # Get type base (e.g., int, double, char, struct X)
        t = Type()
        if not self.typeBase(t):
            self.restore(startPos)
            return False

        # Get variable name
        tkName = self.consume("ID")
        if not tkName:
            self.restore(startPos)
            return False

        # Check for array declaration
        if not self.arrayDecl(t):
            # Not an array
            t.nElements = -1

        # Add the variable to symbol table
        self.add_var(tkName, t)

        # Check for additional variables (comma-separated)
        while True:
            if not self.consume("COMMA"):
                break

            tkName = self.consume("ID")
            if not tkName:
                raise SyntaxError("Expected variable name after comma")

            # Reset the type for the new variable
            t_new = Type()
            t_new.typeBase = t.typeBase
            t_new.s = t.s

            # Check for array declaration
            if not self.arrayDecl(t_new):
                # Not an array
                t_new.nElements = -1

            # Add the variable to symbol table
            self.add_var(tkName, t_new)

        # Require semicolon at end
        if not self.consume("SEMICOLON"):
            self.restore(startPos)
            return False

        return True

    def typeBase(self, ret):
        """Parse a type base and store it in ret"""
        print("Checking typeBase")
        startPos = self.save()

        if self.consume("INT"):
            print("Found INT")
            ret.typeBase = "TB_INT"
            return True

        self.restore(startPos)
        if self.consume("DOUBLE"):
            print("Found DOUBLE")
            ret.typeBase = "TB_DOUBLE"
            return True

        self.restore(startPos)
        if self.consume("CHAR"):
            print("Found CHAR")
            ret.typeBase = "TB_CHAR"
            return True

        self.restore(startPos)
        if self.consume("VOID"):
            print("Found VOID")
            ret.typeBase = "TB_VOID"
            return True

        # Check for struct type
        self.restore(startPos)
        if self.consume("STRUCT"):
            tkName = self.consume("ID")
            if not tkName:
                self.restore(startPos)
                return False

            # Semantic action: Check that struct exists
            s = find_symbol(symbols, tkName.text)
            if s is None:
                tkerr(self.crtTk, "undefined symbol: %s", tkName.text)
            if s.cls != "CLS_STRUCT":
                tkerr(self.crtTk, "%s is not a struct", tkName.text)

            ret.typeBase = "TB_STRUCT"
            ret.s = s
            return True

        self.restore(startPos)
        print("typeBase failed")
        return False

    def arrayDecl(self, ret):
        """Parse array declaration and update type"""
        if not self.consume("LBRACKET"):
            return False

        # Array size is optional
        startPos = self.save()
        if self.expr():
            # For now, just mark as array without computing size
            ret.nElements = 0

        if not self.consume("RBRACKET"):
            raise SyntaxError("Expected ] in array declaration")

        return True

    def typeName(self, ret):
        """Parse a type name (base type + optional array)"""
        if not self.typeBase(ret):
            return False

        if not self.arrayDecl(ret):
            ret.nElements = -1

        return True

    def declFunc(self):
        """Parse function declaration with semantic analysis"""
        print("Checking declFunc")
        startPos = self.save()

        # Get return type (typeBase or void)
        t = Type()
        void_type = self.consume("VOID")
        if void_type:
            t.typeBase = "TB_VOID"
        else:
            if not self.typeBase(t):
                self.restore(startPos)
                return False

            # Check for pointer return type
            if self.consume("MUL"):
                t.nElements = 0  # Mark as pointer
            else:
                t.nElements = -1  # Not an array/pointer

        # Get function name
        tkName = self.consume("ID")
        if not tkName:
            self.restore(startPos)
            return False

        # Start of parameter list
        if not self.consume("LPAR"):
            self.restore(startPos)
            return False

        # Semantic action: check for redefinition and create func symbol
        global crtFunc, crtDepth
        if find_symbol(symbols, tkName.text):
            tkerr(self.crtTk, "symbol redefinition: %s", tkName.text)
        crtFunc = add_symbol(symbols, tkName.text, "CLS_FUNC")
        crtFunc.args = SymbolTable()
        crtFunc.args.init_symbols()
        crtFunc.type = t
        crtDepth += 1

        # Parse function arguments
        if self.funcArg():
            while self.consume("COMMA"):
                if not self.funcArg():
                    raise SyntaxError("Expected function argument after comma")

        # End of parameter list
        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) to close function parameters")

        # Decrease depth before function body
        crtDepth -= 1

        # Function body
        if not self.stmCompound():
            raise SyntaxError("Expected function body { ... }")

        # Clean up symbols after function declaration
        delete_symbols_after(symbols, crtFunc)
        crtFunc = None

        return True

    def funcArg(self):
        """Parse function argument with semantic analysis"""
        startPos = self.save()

        # Get parameter type
        t = Type()
        if not self.typeBase(t):
            self.restore(startPos)
            return False

        # Get parameter name
        tkName = self.consume("ID")
        if not tkName:
            self.restore(startPos)
            return False

        # Check for array parameter
        if not self.arrayDecl(t):
            t.nElements = -1

        # Semantic action: add parameter to symbol table
        s = add_symbol(symbols, tkName.text, "CLS_VAR")
        s.mem = "MEM_ARG"
        s.type = t

        # Also add to function args
        s = add_symbol(crtFunc.args, tkName.text, "CLS_VAR")
        s.mem = "MEM_ARG"
        s.type = t

        return True

    def stm(self):
        """Parse a statement"""
        startPos = self.save()

        # Try each statement type
        if self.stmCompound():
            return True

        self.restore(startPos)
        if self.stmIf():
            return True

        self.restore(startPos)
        if self.stmWhile():
            return True

        self.restore(startPos)
        if self.stmFor():
            return True

        self.restore(startPos)
        if self.stmBreak():
            return True

        self.restore(startPos)
        if self.stmReturn():
            return True

        self.restore(startPos)
        if self.stmAssign():
            return True

        self.restore(startPos)
        if self.stmExpr():
            return True

        return False

    def stmCompound(self):
        """Parse compound statement (block) with semantic analysis"""
        if not self.consume("LACC"):
            return False

        # Save the last symbol for later cleanup
        global crtDepth
        start = symbols.begin[-1] if symbols.begin else None

        # Enter new scope
        crtDepth += 1

        # Process declarations and statements inside the block
        while True:
            startPos = self.save()

            if self.declVar():
                continue

            self.restore(startPos)
            if self.stm():
                continue

            break  # No more declarations or statements

        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close compound statement")

        # Exit scope and clean up symbols
        crtDepth -= 1
        delete_symbols_after(symbols, start)

        return True

    def expr(self):
        startPos = self.save()
        if self.exprAssign():
            return True
        self.restore(startPos)
        return False

    def stmExpr(self):
        startPos = self.save()
        if not self.expr():
            return False
        if not self.consume("SEMICOLON"):
            self.restore(startPos)
            return False
        return True

    def exprAssign(self):
        startPos = self.save()

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
        """Parse primary expression (variable, constant, function call, etc.)"""
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
        startPos = self.save()

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
            self.restore(startPos)
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