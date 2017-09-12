import sys
import lexleader
import os
import unittest
from subprocess import Popen, PIPE
from pyminisolvers import minisolvers
from random import randint

test_set = ["and", "and-cse", "or", "or-cse", "ror", "alpha", "alpha-m", "harvey"]


class TestLexLeader(unittest.TestCase):
    # https://stackoverflow.com/a/13606054
    def repeat(times):
        def repeatHelper(f):
            def callHelper(*args):
                for i in range(0, times):
                    f(*args)
            return callHelper
        return repeatHelper

    def test_corner(self):
        less = [[[0,0], [0,1]], [[0,0], [1,1]], [[0,1], [1,1]],
                [[0,0], [1,0]], [[1,0], [1,1]]]
        equal = [[[0,0], [0,0]], [[1,1], [1,1]], [[1,0],[1,0]], [[0,1], [0,1]]]
        greater = [[[1,0], [0,1]], [[1,1], [0,1]], [[1,1], [0,0]], [[0,1], [0,0]],
                   [[1,0], [0,0]], [[1,1], [1,0]], [[1,1], [0,1]]]
        for each in test_set:
            for model in less+equal:
                self.assertTrue(self.check_lex(2, 2, each, model))

            for non_lex in greater:
                self.assertFalse(self.check_lex(2, 2, each, non_lex))

    def test_square(self):
        for each in test_set:
            for i in range(2, 21):
                model = self.generate_model(i, i)
                self.assertTrue(self.check_lex(i, i, each, model))

    def test_two_by_x(self):
        for each in test_set:
            for i in [10, 100, 1000]:
                model = self.generate_model(2, i)
                self.assertTrue(self.check_lex(2, i, each, model))

    def test_x_by_two(self):
        for each in test_set:
            for i in [10, 1000]:
                model = self.generate_model(i, 2)
                self.assertTrue(self.check_lex(i, 2, each, model))

    @repeat(100)
    def test_random_sat(self):
        num_c = randint(2, 10)
        num_r = randint(2, 10)
        model = self.generate_model(num_c, num_r)
        for each in test_set:
            self.assertTrue(self.check_lex(num_c, num_r, each, model))

    @repeat(100)
    def test_random_unsat(self):
        num_c = randint(2, 10)
        num_r = randint(2, 10)
        model = self.generate_model(num_c, num_r)
        while len(set(model)) == 1:  # so that all vectors are not identical
            model = self.generate_model(num_c, num_r)
        for each in test_set:
            non_lex = model[::-1]
            # print(each)
            # print("---", model)
            # print("===", non_lex)
            self.assertFalse(self.check_lex(num_c, num_r, each, non_lex))

    def make_assumps(self, complete, num_c, num_r, lex):
            assumps = ""
            for i in range(num_c):
                for j in range(num_r):
                    if complete[i][j] is 1:
                        assump = lex.varmap[(i, j)]
                    else:
                        assump = -lex.varmap[(i, j)]
                    assumps += lex.add_assumps(assump)
            return assumps

    def compare_lex(self, vector):
        total = 0
        for x in range(len(vector)):
            total += (vector[-(x+1)] << x)
        # print(vector, total)  # for debugging
        return total

    def generate_model(self, num_c, num_r):
        full = []
        for i in range(num_c):
            vertor = []
            for i in range(num_r):
                vertor.append(randint(0, 1))
            full.append(tuple(vertor))
        return sorted(full, key=lambda vector: self.compare_lex(vector))

    def check_lex(self, num_c, num_r, option, assignment):
        lex = lexleader.LexLeader(num_c, num_r, option, rows_enabled=False)
        lex_constraints = lex.make_lexleader()
        assumps = self.make_assumps(assignment, num_c, num_r, lex)
        cnf = self.get_cnf(lex_constraints+assumps)
        solver = minisolvers.MinicardSolver()
        self.parse_dimacs(cnf, solver)
        return solver.solve()

    def get_cnf(self, formula):
        pathtofile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bool2cnf')
        p = Popen(pathtofile, stdout=PIPE, stdin=PIPE)
        stdout, _ = p.communicate(input=formula.encode('utf-8'))
        return stdout.decode("utf-8").split('\n')

    def parse_dimacs(self, f, solver):
        i = 0
        for line in f:
            if line.startswith('p'):
                tokens = line.split()
                nvars = int(tokens[2])
                nclauses = int(tokens[3])

                while solver.nvars() < nvars:
                    solver.new_var()
                continue  # skip parsing the first line
            if line == "":
                continue  # skip parsing the last line
            lits = line.split()

            clause = [int(x) for x in lits[:-1]]
            solver.add_clause(clause)

            i += 1
        assert i == nclauses

if __name__ == '__main__':
    unittest.main()
