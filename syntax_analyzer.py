class Token:
    def __init__(self, code, value=None, next_token=None, text=None, line=None):
        self.code = code  # Token type (e.g., 'ID', 'CT_INT', etc.)
        self.type = code  # Add this line to make it compatible with PLY
        self.value = value
        self.text = text if text is not None else value  # Store the token text
        self.next = next_token
        self.line = line  # Line number for error reporting
        # For specific token types
        self.i = None  # For integer and char constants
        self.r = None  # For real constants


class Type:
    def __init__(self):
        self.typeBase = None  # TB_INT, TB_DOUBLE, TB_CHAR, TB_VOID, TB_STRUCT
        self.nElements = -1  # -1 for non-array, 0 for arrays with unknown size, >0 for arrays with known size
        self.s = None  # Symbol reference for struct types

    def copy(self):
        """Create a deep copy of this Type object"""
        t = Type()
        t.typeBase = self.typeBase
        t.nElements = self.nElements
        t.s = self.s  # Reference to the same symbol
        return t


class Symbol:
    def __init__(self, name, cls):
        self.name = name  # Symbol name
        self.cls = cls  # CLS_VAR, CLS_FUNC, CLS_STRUCT, CLS_EXTFUNC
        self.depth = 0  # Symbol scope depth
        self.mem = None  # MEM_GLOBAL, MEM_LOCAL, MEM_ARG
        self.type = Type()  # Symbol type
        self.args = None  # For functions: list of argument symbols
        self.members = None  # For structs: list of member symbols


class RetVal:
    def __init__(self):
        self.type = Type()  # Type of the result
        self.isLVal = False  # If it is a LVal
        self.isCtVal = False  # If it is a constant value
        self.ctVal = None  # The constant value (can be int, double, char, or str)


class SymbolTable:
    def __init__(self):
        self.begin = []  # List of symbols
        self.end = []  # End marker for each depth level

    def init_symbols(self):
        self.begin = []
        self.end = [None]  # Initial end marker


class SemanticError(Exception):
    """Exception for semantic errors"""
    pass


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


def create_type(type_base, n_elements):
    """Create a new type with specified base type and number of elements"""
    t = Type()
    t.typeBase = type_base
    t.nElements = n_elements
    return t


def tkerr(tk, msg, *args):
    """Report a semantic error"""
    formatted_msg = msg % args if args else msg
    line_info = f" at line {tk.line}" if hasattr(tk, 'line') else ""
    raise SemanticError(f"{formatted_msg}{line_info}")


def cast(dst, src):
    """Try to convert src type to dst type according to AtomC rules"""
    # Check array conversions
    if src.nElements > -1:  # src is an array
        if dst.nElements > -1:  # dst is also an array
            if src.typeBase != dst.typeBase:
                tkerr(crtTk, "an array cannot be converted to an array of another type")
        else:  # dst is not an array
            tkerr(crtTk, "an array cannot be converted to a non-array")
    else:  # src is not an array
        if dst.nElements > -1:  # dst is an array
            tkerr(crtTk, "a non-array cannot be converted to an array")

    # Check type conversions
    if src.typeBase in ["TB_CHAR", "TB_INT", "TB_DOUBLE"]:
        if dst.typeBase in ["TB_CHAR", "TB_INT", "TB_DOUBLE"]:
            return  # Arithmetic types can be converted to any other arithmetic type

    # Check struct conversions
    if src.typeBase == "TB_STRUCT":
        if dst.typeBase == "TB_STRUCT":
            if src.s != dst.s:
                tkerr(crtTk, "a structure cannot be converted to another one")
            return

    # If we get here, no conversion is possible
    tkerr(crtTk, "incompatible types")


def get_arith_type(s1, s2):
    """Get the result type from an arithmetic operation on two types"""
    # Check if both operands are arithmetic types
    if s1.typeBase not in ["TB_CHAR", "TB_INT", "TB_DOUBLE"] or \
            s2.typeBase not in ["TB_CHAR", "TB_INT", "TB_DOUBLE"]:
        tkerr(crtTk, "operands must be of arithmetic type")

    # Return the "wider" type (double > int > char)
    if s1.typeBase == "TB_DOUBLE" or s2.typeBase == "TB_DOUBLE":
        return create_type("TB_DOUBLE", -1)
    if s1.typeBase == "TB_INT" or s2.typeBase == "TB_INT":
        return create_type("TB_INT", -1)
    return create_type("TB_CHAR", -1)


def add_ext_func(symbols, name, type_base, n_elements=-1):
    """Add an external function to the symbol table"""
    s = add_symbol(symbols, name, "CLS_EXTFUNC")
    s.type = create_type(type_base, n_elements)
    s.args = SymbolTable()
    s.args.init_symbols()
    return s


def add_func_arg(func, name, type_base, n_elements=-1):
    """Add an argument to a function symbol"""
    a = add_symbol(func.args, name, "CLS_VAR")
    a.type = create_type(type_base, n_elements)
    a.mem = "MEM_ARG"
    return a


def add_ext_funcs(symbols):
    """Add predefined functions to symbol table"""
    # void put_s(char s[])
    s = add_ext_func(symbols, "put_s", "TB_VOID")
    add_func_arg(s, "s", "TB_CHAR", 0)

    # void get_s(char s[])
    s = add_ext_func(symbols, "get_s", "TB_VOID")
    add_func_arg(s, "s", "TB_CHAR", 0)

    # void put_i(int i)
    s = add_ext_func(symbols, "put_i", "TB_VOID")
    add_func_arg(s, "i", "TB_INT", -1)

    # int get_i()
    s = add_ext_func(symbols, "get_i", "TB_INT")

    # void put_d(double d)
    s = add_ext_func(symbols, "put_d", "TB_VOID")
    add_func_arg(s, "d", "TB_DOUBLE", -1)

    # double get_d()
    s = add_ext_func(symbols, "get_d", "TB_DOUBLE")

    # void put_c(char c)
    s = add_ext_func(symbols, "put_c", "TB_VOID")
    add_func_arg(s, "c", "TB_CHAR", -1)

    # char get_c()
    s = add_ext_func(symbols, "get_c", "TB_CHAR")

    # double seconds()
    s = add_ext_func(symbols, "seconds", "TB_DOUBLE")


# Global variables for semantic analysis
symbols = SymbolTable()
crtDepth = 0
crtFunc = None
crtStruct = None
crtTk = None  # Current token for error reporting


def init_globals():
    global symbols, crtDepth, crtFunc, crtStruct, crtTk
    symbols = SymbolTable()
    symbols.init_symbols()
    crtDepth = 0
    crtFunc = None
    crtStruct = None
    crtTk = None
    # Initialize predefined functions
    add_ext_funcs(symbols)


class Parser:
    def __init__(self, tokens):
        self.crtTk = tokens  # Current token
        global crtTk
        crtTk = tokens  # Set global current token for error reporting
        init_globals()  # Initialize semantic analysis globals

    def save(self):
        """Save current token position for backtracking"""
        return self.crtTk

    def restore(self, saved_pos):
        """Restore to previously saved position"""
        self.crtTk = saved_pos
        global crtTk
        crtTk = saved_pos  # Update global token pointer too

    def consume(self, code):
        print(f"Trying to consume: {code}, Current token: {self.crtTk.code if self.crtTk else 'None'}")
        if self.crtTk and self.crtTk.code == code:
            last_consumed = self.crtTk
            self.crtTk = self.crtTk.next
            global crtTk
            crtTk = self.crtTk  # Update global token pointer too
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

        # Create a deep copy of the type for the variable
        s.type = t.copy()
        # Ensure array type is properly preserved
        s.type.nElements = t.nElements
        print(f"Added variable: {tkName.text}, type: {t.typeBase}, nElements: {t.nElements}")
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

        # Check for array declaration for the first variable
        current_type = t.copy()  # Create a copy to avoid modifying the original
        if not self.arrayDecl(current_type):
            current_type.nElements = -1  # Not an array

        # Add the first variable
        self.add_var(tkName, current_type)

        # Process additional variables separated by commas
        while self.consume("COMMA"):
            tkName = self.consume("ID")
            if not tkName:
                raise SyntaxError("Expected variable name after comma")

            # Create a new type for each variable
            var_type = t.copy()  # Start with the base type
            if not self.arrayDecl(var_type):
                var_type.nElements = -1  # Not an array

            # Add the variable to the symbol table
            self.add_var(tkName, var_type)

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

        # Evaluate the array size expression
        rv = RetVal()
        if self.expr(rv):
            # Check if the expression is a constant integer
            if not rv.isCtVal:
                tkerr(self.crtTk, "the array size is not a constant")
            if rv.type.typeBase != "TB_INT":
                tkerr(self.crtTk, "the array size is not an integer")
            ret.nElements = int(rv.ctVal)  # Cast to integer
            print(f"Array size evaluated as constant: {ret.nElements}")
        else:
            tkerr(self.crtTk, "invalid array size expression")

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
        crtFunc.type = t.copy()  # Deep copy the type
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
        s.type = t.copy()  # Deep copy the type

        # Also add to function args
        s = add_symbol(crtFunc.args, tkName.text, "CLS_VAR")
        s.mem = "MEM_ARG"
        s.type = t.copy()  # Deep copy the type

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
        if self.stmExpr():
            return True

        return False

    def stmCompound(self):
        if not self.consume("LACC"):
            return False

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

            break

        if not self.consume("RACC"):
            raise SyntaxError("Expected } to close compound statement")

        # Exit scope and clean up symbols only if not the function body
        if crtDepth > 1:  # Assuming function body is at depth 1
            crtDepth -= 1
            delete_symbols_after(symbols, start)

        return True

    def expr(self, rv):
        """Parse an expression and set its RetVal"""
        return self.exprAssign(rv)

    def stmExpr(self):
        """Parse an expression statement (expr;)"""
        startPos = self.save()

        # Optional expression
        rv = RetVal()
        self.expr(rv)  # We don't check the return since it's optional

        if not self.consume("SEMICOLON"):
            self.restore(startPos)
            return False
        return True

    def exprAssign(self, rv):
        """Parse an assignment expression"""
        startPos = self.save()

        # Check for unary expression (potential lvalue)
        if not self.exprOr(rv):
            self.restore(startPos)
            return False

        # If followed by assignment, it's an assignment expression
        if self.consume("ASSIGN"):
            rve = RetVal()
            if not self.exprAssign(rve):
                raise SyntaxError("Expected expression after =")

            # Check if left side is an lvalue
            if not rv.isLVal:
                tkerr(self.crtTk, "cannot assign to a non-lval")

            # Check for array assignment
            if rv.type.nElements > -1 or rve.type.nElements > -1:
                tkerr(self.crtTk, "the arrays cannot be assigned")

            # Try to cast right to left type
            cast(rv.type, rve.type)

            # Result is not a constant or lvalue
            rv.isCtVal = rv.isLVal = False

            return True

        # Restore token position for backtracking
        self.restore(startPos)

        # Try as a regular OR expression
        return self.exprOr(rv)

    def exprOr(self, rv):
        """Parse a logical OR expression"""
        if not self.exprAnd(rv):
            return False

        while self.consume("OR"):
            rve = RetVal()
            if not self.exprAnd(rve):
                raise SyntaxError("Expected expression after OR")

            # Check if operands are structures
            if rv.type.typeBase == "TB_STRUCT" or rve.type.typeBase == "TB_STRUCT":
                tkerr(self.crtTk, "a structure cannot be logically tested")

            # Result is always int
            rv.type = create_type("TB_INT", -1)
            rv.isCtVal = rv.isLVal = False

        return True

    def exprAnd(self, rv):
        """Parse a logical AND expression"""
        if not self.exprEq(rv):
            return False

        while self.consume("AND"):
            rve = RetVal()
            if not self.exprEq(rve):
                raise SyntaxError("Expected expression after AND")

            # Check if operands are structures
            if rv.type.typeBase == "TB_STRUCT" or rve.type.typeBase == "TB_STRUCT":
                tkerr(self.crtTk, "a structure cannot be logically tested")

            # Result is always int
            rv.type = create_type("TB_INT", -1)
            rv.isCtVal = rv.isLVal = False

        return True

    def exprEq(self, rv):
        """Parse an equality expression"""
        if not self.exprRel(rv):
            return False

        while self.consume("EQUAL") or self.consume("NOTEQ"):
            rve = RetVal()
            if not self.exprRel(rve):
                raise SyntaxError("Expected expression after equality operator")

            # Semantic action: Check types and compute result
            if rv.type.typeBase == "TB_STRUCT" or rve.type.typeBase == "TB_STRUCT":
                tkerr(self.crtTk, "a structure cannot be compared")

            # Convert operands to common type
            t = get_arith_type(rv.type, rve.type)

            # Result is always int
            rv.type = create_type("TB_INT", -1)
            rv.isCtVal = rv.isLVal = False

        return True

    def exprRel(self, rv):
        """Parse a relational expression"""
        if not self.exprAdd(rv):
            return False

        while self.consume("LESS") or self.consume("LESSEQ") or \
                self.consume("GREATER") or self.consume("GREATEREQ"):
            rve = RetVal()
            if not self.exprAdd(rve):
                raise SyntaxError("Expected expression after relational operator")

            # Semantic action: Check types and compute result
            if rv.type.typeBase == "TB_STRUCT" or rve.type.typeBase == "TB_STRUCT":
                tkerr(self.crtTk, "a structure cannot be compared")

            # Convert operands to common type
            t = get_arith_type(rv.type, rve.type)

            # Result is always int
            rv.type = create_type("TB_INT", -1)
            rv.isCtVal = rv.isLVal = False

        return True

    def exprAdd(self, rv):
        """Parse an additive expression (+ or -)"""
        if not self.exprMul(rv):
            return False

        while True:
            add_op = self.consume("ADD")
            sub_op = self.consume("SUB")
            if not (add_op or sub_op):
                break

            rve = RetVal()
            if not self.exprMul(rve):
                raise SyntaxError("Expected expression after additive operator")

            # Constant folding for addition/subtraction
            if rv.isCtVal and rve.isCtVal:
                if add_op:
                    rv.ctVal += rve.ctVal
                else:
                    rv.ctVal -= rve.ctVal
            else:
                rv.isCtVal = False

            # Type checking
            if rv.type.typeBase == "TB_STRUCT" or rve.type.typeBase == "TB_STRUCT":
                tkerr(self.crtTk, "a structure cannot be used in arithmetic operations")

            # Update result type
            rv.type = get_arith_type(rv.type, rve.type)
            rv.isLVal = False

        return True

    def exprMul(self, rv):
        """Parse a multiplicative expression (* or /)"""
        if not self.exprCast(rv):
            return False

        while True:
            mul_op = self.consume("MUL")
            div_op = self.consume("DIV")
            if not (mul_op or div_op):
                break

            rve = RetVal()
            if not self.exprCast(rve):
                raise SyntaxError("Expected expression after multiplicative operator")

            # Constant folding for multiplication/division
            if rv.isCtVal and rve.isCtVal:
                if mul_op:
                    rv.ctVal *= rve.ctVal
                elif div_op:
                    if rve.ctVal == 0:
                        tkerr(self.crtTk, "division by zero")
                    rv.ctVal = int(rv.ctVal / rve.ctVal)  # Integer division
            else:
                rv.isCtVal = False

            # Type checking
            if rv.type.typeBase == "TB_STRUCT" or rve.type.typeBase == "TB_STRUCT":
                tkerr(self.crtTk, "a structure cannot be used in arithmetic operations")

            # Update result type
            rv.type = get_arith_type(rv.type, rve.type)
            rv.isLVal = False

        return True

    def exprCast(self, rv):
        """Parse a cast expression"""
        startPos = self.save()

        if self.consume("LPAR"):
            t = Type()
            if self.typeName(t):
                if self.consume("RPAR"):
                    if self.exprCast(rv):
                        # Try to cast the value to the specified type
                        cast(t, rv.type)
                        rv.type = t.copy()  # Use a deep copy of the type
                        rv.isLVal = False
                        return True

        # If cast didn't match, try unary expression
        self.restore(startPos)
        return self.exprUnary(rv)

    def exprUnary(self, rv):
        """Parse a unary expression"""
        if self.consume("SUB"):
            if not self.exprUnary(rv):
                raise SyntaxError("Expected expression after unary -")

            # Check if operand is numeric
            if rv.type.typeBase not in ["TB_INT", "TB_CHAR", "TB_DOUBLE"]:
                tkerr(self.crtTk, "unary - requires numeric operand")

            rv.isLVal = False
            return True

        if self.consume("NOT"):
            if not self.exprUnary(rv):
                raise SyntaxError("Expected expression after unary !")

            # Check if operand is arithmetic
            if rv.type.typeBase not in ["TB_INT", "TB_CHAR", "TB_DOUBLE"]:
                tkerr(self.crtTk, "unary ! requires arithmetic operand")

            rv.type = create_type("TB_INT", -1)
            rv.isLVal = rv.isCtVal = False
            return True

        return self.exprPostfix(rv)

    def exprPostfix(self, rv):
        """Parse a postfix expression (array access, struct member, function call)"""
        if not self.exprPrimary(rv):
            return False

        while True:
            # Array access
            if self.consume("LBRACKET"):
                rve = RetVal()
                if not self.expr(rve):
                    raise SyntaxError("Expected expression inside [ ]")

                if not self.consume("RBRACKET"):
                    raise SyntaxError("Expected ] after array index")

                # Check array indexing semantics
                if rv.type.nElements == -1:
                    tkerr(self.crtTk, "indexed operand is not an array")

                if rve.type.typeBase not in ["TB_INT", "TB_CHAR"]:
                    tkerr(self.crtTk, "array index must be an integer")

                # Result type is the element type of the array
                rv.type.nElements = -1
                rv.isLVal = True
                rv.isCtVal = False

            # Struct member access
            elif self.consume("DOT"):
                tkName = self.consume("ID")
                if not tkName:
                    raise SyntaxError("Expected field name after .")

                # Check struct member access semantics
                if rv.type.typeBase != "TB_STRUCT":
                    tkerr(self.crtTk, "accessing a member of a non-struct")

                s = find_symbol(rv.type.s.members, tkName.text)
                if not s:
                    tkerr(self.crtTk, "undefined struct member: %s", tkName.text)

                # Result type is the member's type
                rv.type = s.type
                rv.isLVal = True
                rv.isCtVal = False

            # Function call
            elif self.consume("LPAR"):
                # Check that the symbol is a function
                if not hasattr(rv, 'symbol') or rv.symbol.cls not in ["CLS_FUNC", "CLS_EXTFUNC"]:
                    tkerr(self.crtTk, "calling a non-function: %s",
                          rv.symbol.name if hasattr(rv, 'symbol') else "<unknown>")

                args = []  # Collect argument types for validation

                # Parse arguments
                if self.crtTk.code != "RPAR":
                    rve = RetVal()
                    if not self.expr(rve):
                        raise SyntaxError("Expected expression in function arguments")
                    args.append(rve)

                    while self.consume("COMMA"):
                        rve = RetVal()
                        if not self.expr(rve):
                            raise SyntaxError("Expected expression after comma")
                        args.append(rve)

                if not self.consume("RPAR"):
                    raise SyntaxError("Expected ) in function call")

                # Check arguments against function definition
                # (simplified validation for now)

                # Result type is the function's return type
                rv.type = rv.symbol.type.copy()  # Return type (e.g., TB_INT)
                rv.isLVal = False
                rv.isCtVal = False

            else:
                # No more postfix operators
                break

        return True

    def exprPrimary(self, rv):
        """Parse primary expression (variable, constant, parenthesized expression)"""
        # ID - variable, function, etc.
        tkName = self.consume("ID")
        if tkName:
            # Find symbol in the symbol table
            s = find_symbol(symbols, tkName.text)
            if not s:
                # Handle undefined variables more gracefully
                if self.crtTk and self.crtTk.code == "ASSIGN" and crtFunc:
                    # Auto-declare variable if it's being assigned in a function
                    s = add_symbol(symbols, tkName.text, "CLS_VAR")
                    s.mem = "MEM_LOCAL"
                    s.type = create_type("TB_INT", -1)  # Default to int
                else:
                    tkerr(self.crtTk, "undefined symbol: %s", tkName.text)

            # Store the symbol in RetVal for later checks
            rv.symbol = s  # <-- Add this line

            # Set return value based on symbol type
            if s.cls == "CLS_VAR":
                rv.type = s.type.copy()
                rv.isLVal = True
                rv.isCtVal = False
            elif s.cls in ["CLS_FUNC", "CLS_EXTFUNC"]:
                rv.type = s.type.copy()
                rv.isLVal = False
                rv.isCtVal = False
            else:
                tkerr(self.crtTk, "invalid symbol usage: %s", tkName.text)

            return True


        # Integer constant
        tkInt = self.consume("CT_INT")
        if tkInt:
            rv.type = create_type("TB_INT", -1)
            rv.isCtVal = True
            rv.isLVal = False
            rv.ctVal = int(tkInt.value)
            return True

        # Real constant
        tkReal = self.consume("CT_REAL")
        if tkReal:
            rv.type = create_type("TB_DOUBLE", -1)
            rv.isCtVal = True
            rv.isLVal = False
            rv.ctVal = float(tkReal.value)
            return True

        # Character constant
        tkChar = self.consume("CT_CHAR")
        if tkChar:
            rv.type = create_type("TB_CHAR", -1)
            rv.isCtVal = True
            rv.isLVal = False
            rv.ctVal = tkChar.value
            return True

        # String constant
        tkString = self.consume("CT_STRING")
        if tkString:
            rv.type = create_type("TB_CHAR", 0)  # Array of chars
            rv.isCtVal = True
            rv.isLVal = False
            rv.ctVal = tkString.value
            return True

        # Parenthesized expression
        if self.consume("LPAR"):
            if not self.expr(rv):
                raise SyntaxError("Expected expression after (")
            if not self.consume("RPAR"):
                raise SyntaxError("Expected )")
            return True

        return False

    def stmIf(self):
        """Parse if statement with semantic analysis"""
        if not self.consume("IF"):
            return False

        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( after if")

        rv = RetVal()
        if not self.expr(rv):
            raise SyntaxError("Expected condition in if statement")

        # Check if condition is valid for logical test
        if rv.type.typeBase == "TB_STRUCT":
            tkerr(self.crtTk, "a structure cannot be logically tested")

        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) after if condition")

        if not self.stm():
            raise SyntaxError("Expected statement for if block")

        if self.consume("ELSE"):
            if not self.stm():
                raise SyntaxError("Expected statement for else block")

        return True

    def stmWhile(self):
        """Parse while statement with semantic analysis"""
        if not self.consume("WHILE"):
            return False

        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( after while")

        rv = RetVal()
        if not self.expr(rv):
            raise SyntaxError("Expected condition in while statement")

        # Check if condition is valid for logical test
        if rv.type.typeBase == "TB_STRUCT":
            tkerr(self.crtTk, "a structure cannot be logically tested")

        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) after while condition")

        if not self.stm():
            raise SyntaxError("Expected statement for while block")

        return True

    def stmFor(self):
        """Parse for statement with semantic analysis"""
        if not self.consume("FOR"):
            return False

        if not self.consume("LPAR"):
            raise SyntaxError("Expected ( after for")

        # Expression 1 (initialization) - optional
        rv = RetVal()
        self.expr(rv)  # We don't check the return since it's optional

        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after for initialization")

        # Expression 2 (condition) - optional
        if self.crtTk.code != "SEMICOLON":
            rv = RetVal()
            if self.expr(rv):
                # Check if condition is valid for logical test
                if rv.type.typeBase == "TB_STRUCT":
                    tkerr(self.crtTk, "a structure cannot be logically tested")

        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after for condition")

        # Expression 3 (increment) - optional
        rv = RetVal()
        self.expr(rv)  # Optional

        if not self.consume("RPAR"):
            raise SyntaxError("Expected ) after for loop")

        if not self.stm():
            raise SyntaxError("Expected statement for for block")

        return True

    def stmBreak(self):
        """Parse break statement"""
        if not self.consume("BREAK"):
            return False

        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after break")

        return True

    def stmReturn(self):
        """Parse return statement with semantic analysis"""
        if not self.consume("RETURN"):
            return False

        # Return value is optional
        if self.crtTk.code != "SEMICOLON":
            rv = RetVal()
            if self.expr(rv):
                # Check if return type matches function return type
                if crtFunc:
                    cast(crtFunc.type, rv.type)

        if not self.consume("SEMICOLON"):
            raise SyntaxError("Expected ; after return")

        return True