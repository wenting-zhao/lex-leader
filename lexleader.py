import sys


class LexLeader:
    def __init__(self, columns, rows, option="and"):
        self.num_columns = columns
        self.num_rows = rows
        self.parse_option(option)
        self.varmap = dict()
        self.num_var = 0
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

    def print_lexleader(self):
        """ prints out the row and column lex-leader constraints of the full matrix
        """
        full = []
        for c in range(self.num_columns-1):
            column1 = [self.varmap[(c, r)] for r in range(self.num_rows)]
            column2 = [self.varmap[(c+1, r)] for r in range(self.num_rows)]
            full.append(self.which_lex(column1, column2))
        for r in range(self.num_rows-1):
            row1 = [self.varmap[(c, r)] for c in range(self.num_columns)]
            row2 = [self.varmap[(c, r+1)] for c in range(self.num_columns)]
            full.append(self.which_lex(row1, row2))
        print ("\n& ".join(full))

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
            res.append( "({} -> (!x{} & x{}))".format(temp, A[i+1], B[i+1]) )

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
        A = [None] + vector1
        B = [None] + vector2

        # creating the extra variables
        X = dict()
        assert len(vector1) == len(vector2)
        for i in range(1, len(vector1)):
            self.num_var += 1
            X[i] = self.num_var

        res = []  # for ANDing each element...
        temp = []  # for ORing each element...

        # A[1] < B[1]
        temp.append( "(!x{} & x{})".format(A[1], B[1]) )
        # 1 <= i <= n-1, X[i] & (A[i+1] < B[i+1]))
        for i in range(1, len(vector1)):
            temp.append( "(x{} & (!x{} & x{}))".format(X[1], A[i+1], B[i+1]) )
        # A[n] = B[n]
        temp.append( "x{}".format(X[len(vector1)-1]) )
        res.append( "("+" | ".join(temp)+")" )

        # X[1] <=> A[1] = B[1]   (thesis, 3.36)
        res.append( "(x{} = (x{} = x{}))".format(X[1], A[1], B[1]) )
        # 1 <= i <= n−1, X[i+1] <=> (X[i] & (A[i+1] = B[i+1]))   (thesis, 3.37)
        for i in range(1, len(vector1)-1):
            res.append( "(x{} = (x{} & (x{} = x{})))".format(X[i+1], X[i], A[i+1], B[i+1]) )

        return "("+"\n& ".join(res)+")"


def main():
    columns = int(sys.argv[1])
    rows = int(sys.argv[2])
    option = sys.argv[3]
    lex = LexLeader(columns, rows, option)
    lex.print_lexleader()

if __name__ == '__main__':
    main()
