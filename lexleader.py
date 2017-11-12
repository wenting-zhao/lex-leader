import sys


class LexLeader:
    def __init__(self, columns, rows, option, columns_enabled=True, rows_enabled=True):
        self.num_columns = columns
        self.num_rows = rows
        self.columns_enabled = columns_enabled
        self.rows_enabled = rows_enabled
        self.varmap = dict()
        self.num_var = 0
        self.parse_option(option)
        for c in range(columns):
            for r in range(rows):
                self.num_var += 1
                self.varmap[(c, r)] = self.num_var

    def parse_option(self, option):
        if option == "and":
            self.which_lex = self._and_helper
        elif option == "and-cse":
            self.which_lex = self._and_subexpr_helper
        elif option == "or":
            self.which_lex = self._or_helper
        elif option == "or-cse":
            self.which_lex = self._or_subexpr_helper
        elif option == "ror":
            self.which_lex = self._ror_helper
        elif option == "alpha":
            self.which_lex = self._alpha_helper
        elif option == "alpha-m":
            self.which_lex = self._alpha_m_helper
        elif option == "harvey":
            self.which_lex = self._harvey_helper

    def make_lexleader(self):
        """ return the row and column lex-leader constraints of the full matrix
        """
        full = []
        if self.columns_enabled:
            for c in range(self.num_columns-1, 0, -1):
                column1 = [self.varmap[(c, r)] for r in range(self.num_rows)]
                column2 = [self.varmap[(c-1, r)] for r in range(self.num_rows)]
                full.append(self.which_lex(column1, column2))
        if self.rows_enabled:
            for r in range(self.num_rows-1, 0, -1):
                row1 = [self.varmap[(c, r)] for c in range(self.num_columns)]
                row2 = [self.varmap[(c, r-1)] for c in range(self.num_columns)]
                full.append(self.which_lex(row1, row2))
        return "\n& ".join(full)

    def add_assumps(self, *variables):
        assumps = []
        for var in variables:
            if var < 0:
                assumps.append("!x{}".format(abs(var)))
            else:
                assumps.append("x{}".format(var))
        return "\n& "+"\n& ".join(assumps)

    def _and_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the plain AND decomposition encoding
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2

        res = []
        res.append( "(!x{} | x{})".format(A[1], B[1]) )

        assert len(vector1) == len(vector2)
        for i in range(1, len(vector1)):
            temp = []
            for j in range(1, i+1):
                temp.append( "(x{} = x{})".format(A[j], B[j]) )
            temp = " & ".join(temp)
            res.append( "({} -> (!x{} | x{}))".format(temp, A[i+1], B[i+1]) )
        return "("+"\n& ".join(res)+")"

    def _and_subexpr_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the AND decomposition encoding using common sub-expression elimination
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2

        # creating the extra variables
        X = dict()
        assert len(vector1) == len(vector2)
        for i in range(1, len(vector1)):
            self.num_var += 1
            X[i] = self.num_var

        res = []

        # A[1] <= B[1]   (thesis, 3.18)
        res.append( "(!x{} | x{})".format(A[1], B[1]) )
        # X[1] <=> (A[1] = B[1])   (thesis, 3.19)
        res.append( "(x{} = (x{} = x{}))".format(X[1], A[1], B[1]) )

        # 1 <= i <= n-2, X[i+1] <=> (X[i] & (A[i+1] = B[i+1]))   (thesis, 3.20)
        for i in range(1, len(vector1)-1):
            res.append( "(x{} = (x{} & (x{} = x{})))".format(X[i+1], X[i], A[i+1], B[i+1]) )
        # i <= i <= n-1, X[i] -> (A[i+1] <= B[i+1])   (thesis, 3.21)
        for i in range(1, len(vector1)):
            res.append( "(x{} -> (!x{} | x{}))".format(X[i], A[i+1], B[i+1]) )

        return "("+"\n& ".join(res)+")"

    def _or_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the plain OR decomposition encoding
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2

        res = []
        res.append( "(!x{} & x{})".format(A[1], B[1]) )

        assert len(vector1) == len(vector2)
        for i in range(1, len(vector1)):
            temp = []
            for j in range(1, i+1):
                temp.append( "(x{} = x{})".format(A[j], B[j]) )
            temp = " & ".join(temp)
            res.append( "({} & (!x{} & x{}))".format(temp, A[i+1], B[i+1]) )

        temp = []
        for i in range(1, len(vector1)+1):
            temp.append( "(x{} = x{})".format(A[i], B[i]) )
        res.append(" & ".join(temp))

        return "("+"\n| ".join(res)+")"

    def _or_subexpr_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the OR decomposition encoding using common sub-expression elimination
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2

        # creating the extra variables
        X = dict()
        assert len(vector1) == len(vector2)
        for i in range(1, len(vector1)+1):
            self.num_var += 1
            X[i] = self.num_var

        res = []  # for ANDing each element...
        temp = []  # for ORing each element...

        n = len(vector1)

        # A[1] < B[1]
        temp.append( "(!x{} & x{})".format(A[1], B[1]) )
        # 1 <= i <= n-1, X[i] & (A[i+1] < B[i+1]))
        for i in range(1, n):
            temp.append( "(x{} & (!x{} & x{}))".format(X[i], A[i+1], B[i+1]) )
        # X[n]
        temp.append( "x{}".format(X[n]) )
        res.append( "("+" | ".join(temp)+")" )

        # X[1] <=> A[1] = B[1]   (thesis, 3.36)
        res.append( "(x{} = (x{} = x{}))".format(X[1], A[1], B[1]) )
        # 1 <= i <= n−1, X[i+1] <=> (X[i] & (A[i+1] = B[i+1]))   (thesis, 3.37)
        for i in range(1, n):
            res.append( "(x{} = (x{} & (x{} = x{})))".format(X[i+1], X[i], A[i+1], B[i+1]) )

        return "("+"\n& ".join(res)+")"

    def _ror_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the recursive OR decomposition encoding using common sub-expression elimination
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2
        assert len(vector1) == len(vector2)
        n = len(vector1)

        # creating the extra variables
        X = dict()
        for i in range(1, len(vector1)+1):
            self.num_var += 1
            X[i] = self.num_var

        res = []
        # X[1]   (thesis, 3.44)
        res.append( "(x{})".format(X[1]) )
        # X[n] <=> (A[n] <= B[n])   (thesis, 3.45)
        res.append( "(x{} = (!x{} | x{}))".format(X[n], A[n], B[n]) )
        # 1 <= i <= n−1, X[n−i] <=> (A[n−i]<B[n−i] | (A[n−i]=B[n−i] & X[n−i+1]))   (thesis, 3.46)
        for i in range(1, n):
            res.append( "(x{0} = ((!x{1} & x{2}) | ((x{1}=x{2}) & x{3})))".format(X[n-i], A[n-i], B[n-i], X[n-i+1]) )

        return "("+"\n& ".join(res)+")"

    def _alpha_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the Alpha encoding using common sub-expression elimination
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2
        assert len(vector1) == len(vector2)
        n = len(vector1)

        # creating the extra variables
        alpha = dict()
        for i in range(len(vector1)+1):
            self.num_var += 1
            alpha[i] = self.num_var

        res = []
        # alpha[0]   (thesis, 3.66)
        res.append( "(x{})".format(alpha[0]) )
        # 0 <= i <= n−1, -alpha[i] -> -a[i+1]   (thesis, 3.67)
        for i in range(n):
            res.append( "(!x{} -> !x{})".format(alpha[i], alpha[i+1]) )
        # 1 <= i <= n, alpha[i] -> (A[i] = B[i])   (thesis, 3.68)
        for i in range(1, n+1):
            res.append( "(x{} -> (x{} = x{}))".format(alpha[i], A[i], B[i]) )
        # 0 <= i <= n−1, ((alpha[i]) & (!alpha[i+1])) -> (A[i+1] < B[i+1])   (thesis, 3.69)
        for i in range(n):
            res.append( "((x{} & !x{}) -> (!x{} & x{}))".format(alpha[i], alpha[i+1], A[i+1], B[i+1]) )
        # 0 <= i <= n−1, alpha[i] -> (A[i+1] <= B[i+1])   (thesis, 3.70)
        for i in range(n):
            res.append( "(x{} -> (!x{} | x{}))".format(alpha[i], A[i+1], B[i+1]) )

        return "("+"\n& ".join(res)+")"

    def _alpha_m_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the Alpha M encoding using common sub-expression elimination
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2
        assert len(vector1) == len(vector2)
        n = len(vector1)

        # creating the extra variables
        alpha = dict()
        for i in range(1, len(vector1)+2):
            self.num_var += 1
            alpha[i] = self.num_var

        res = []
        # alpha[1]   (thesis, 3.81)
        res.append( "(x{})".format(alpha[1]) )
        # 1 <= i <= n, alpha[i] <=> (((A[i] < B[i])|alpha[i+1]) & (A[i]<=B[i]))   (thesis, 3.82)
        for i in range(1, n+1):
            res.append( "(x{0} = (((!x{1} & x{2})|x{3}) & (!x{1} | x{2})))".format(alpha[i], A[i], B[i], alpha[i+1]) )

        return "("+"\n& ".join(res)+")"

    def _harvey_helper(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
            via the Harvey encoding
            inputs:
                vector1, vector2: lists of integers, equivalent lengths,
                                  each representing a vector of variables
            returns:
                string containing the full expression of the lex-leader constraint
        """
        # setup vectors with 1-based indexing to match constraints in the source paper
        A = [None] + vector1
        B = [None] + vector2
        assert len(vector1) == len(vector2)
        n = len(vector1)

        # creating the extra variables
        X = dict()
        for i in range(1, len(vector1)+1):
            self.num_var += 1
            X[i] = self.num_var

        res = []
        # X[1]   (thesis, 3.54)
        res.append( "(x{})".format(X[1]) )
        # X[n] <=> (A[n] < (B[n]+1))   (thesis, 3.55)
        res.append( "(x{} = x{} -> x{})".format(X[n], A[n], B[n]) )
        # 0 <= i <= n−2, X[n−i−1] <=> (A[n−i−1] < (B[n−i−1] + Bool2Int(X[n−i]))),
        # the right-hand side becomes (B+X)(!A+B)(!A+X)
        for i in range(0, len(vector1)-1):
            res.append(
                "(x{XX} = ((x{B} | x{X}) & (!x{A} | x{B}) & (!x{A} | x{X})))".format(
                    X=X[n-i], XX=X[n-i-1], A=A[n-i-1], B=B[n-i-1]
                )
            )

        return "("+"\n& ".join(res)+")"
