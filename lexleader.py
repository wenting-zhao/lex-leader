import sys


class LexLeader:
    def __init__(self, columns, rows):
        self.num_columns = columns
        self.num_rows = rows
        self.varmap = dict()
        self.num_var = 0
        for c in range(columns):
            for r in range(rows):
                self.num_var += 1
                self.varmap[(c, r)] = self.num_var

    def big_and(self):
        # dealing with columns...
        for c in range(self.num_columns-1):
            extra = ''
            if c != 0:
                extra = '& '
            print (extra+"(x{} | !x{})".format(self.varmap[c, 0], self.varmap[c+1, 0]))
            for r in range(1, self.num_rows):
                output = '& ('
                for x in range(r):
                    if x != 0:
                        output += ' & '
                    output += "(x{0} = x{1})".format(self.varmap[c, x], self.varmap[c+1, x])
                output += ') -> '
                output += ("(x{} | !x{})".format(self.varmap[c, r], self.varmap[c+1, r]))
                print (output)

        # dealing with rows...
        for r in range(self.num_rows-1):
            print ("& (x{} | !x{})".format(self.varmap[0, r], self.varmap[0, r+1]))
            for c in range(1, self.num_columns):
                output = '& ('
                for x in range(c):
                    if x != 0:
                        output += ' & '
                    output += "(x{0} = x{1})".format(self.varmap[x, r], self.varmap[x, r+1])
                output += ') -> '
                output += ("(x{} | !x{})".format(self.varmap[c, r], self.varmap[c, r+1]))
                print (output)

    def recursive_and(self):
        """ prints out the row and column lex-leader constraints of the full matrix
            using the AND decomposition encoding using common sub-expression elimination
        """
        res = []
        for c in range(self.num_columns-1):
            column1 = [self.varmap[(c, r)] for r in range(self.num_rows)]
            column2 = [self.varmap[(c+1, r)] for r in range(self.num_rows)]
            res.append(self._helper_recursive_and(column1, column2))
        for r in range(self.num_rows-1):
            row1 = [self.varmap[(c, r)] for c in range(self.num_columns)]
            row2 = [self.varmap[(c, r+1)] for c in range(self.num_columns)]
            res.append(self._helper_recursive_and(row1, row2))
        print ("\n& ".join(res))

    def _helper_recursive_and(self, vector1, vector2):
        """ creates the lex-leader constraints between two vectors of variables
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
        res.append( "(x{} | !x{})".format(A[1], B[1]) )
        # X[1] <=> (A[1] = B[1])   (thesis, 3.19)
        res.append( "(x{} = (x{} = x{}))".format(X[1], A[1], B[1]) )

        # 1 <= i <= n-2 X[i+1] <=> (X[i] & (A[i+1] = B[i+1]))   (thesis, 3.20)
        for i in range(1, len(vector1)-1):
            res.append( "(x{} = (x{} & (x{} = x{})))".format(X[i+1], X[i], A[i+1], B[i+1]) )
        # i <= i <= n-1 X[i] -> (A[i+1] <= B[i+1])   (thesis, 3.21)
        for i in range(1, len(vector1)):
            res.append( "(x{} -> (x{} | !x{}))".format(X[i], A[i+1], B[i+1]) )

        return "\n& ".join(res)

    def big_or(self):
        # dealing with columns...
        for c in range(self.num_columns-1):
            extra = '('
            if c != 0:
                extra = '& ' + extra
            print (extra+"(x{} & !x{})".format(self.varmap[c, 0], self.varmap[c+1, 0]))
            for r in range(self.num_rows-1):
                output = '| ('
                for x in range(r+1):
                    if x != 0:
                        output += ' & '
                    output += "(x{0} = x{1})".format(self.varmap[c, x], self.varmap[c+1, x])
                output += " & (x{} & !x{})".format(self.varmap[c, r+1], self.varmap[c+1, r+1])
                output += ')'
                print (output)
            more = '| ('
            for r in range(self.num_rows):
                if r != 0:
                    more += ' & '
                more += "(x{0} = x{1})".format(self.varmap[c, r], self.varmap[c+1, r])
                if r == self.num_rows-1:
                    more += '))'
            print (more)

        # dealing with rows
        for r in range(self.num_rows-1):
            extra = '& ('
            print (extra+"(x{} & !x{})".format(self.varmap[0, r], self.varmap[0, r+1]))
            for c in range(self.num_columns-1):
                output = '| ('
                for x in range(c+1):
                    if x != 0:
                        output += ' & '
                    output += "(x{0} = x{1})".format(self.varmap[x, r], self.varmap[x, r+1])
                output += " & (x{} & !x{})".format(self.varmap[c+1, r], self.varmap[c+1, r+1])
                output += ')'
                print (output)
            more = '| ('
            for c in range(self.num_columns):
                if c != 0:
                    more += ' & '
                more += "(x{0} = x{1})".format(self.varmap[c, r], self.varmap[c, r+1])
                if c == self.num_columns-1:
                    more += '))'
            print (more)


def main():
    columns = int(sys.argv[1])
    rows = int(sys.argv[2])
    lex = LexLeader(columns, rows)
    lex.recursive_and()

if __name__ == '__main__':
    main()
