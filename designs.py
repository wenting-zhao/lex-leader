#!/usr/bin/env python

import sys
import itertools
import utils
from collections import defaultdict
from pyminisolvers import minisolvers


class Decomp:
    def __init__(self, n, k, copy):
        self.num_v = n
        self.num_k = k
        self.r = copy*(n-1)/(k-1)
        assert self.r == int(self.r)
        self.r = int(self.r)
        self.copy = copy
        self.e_all = list(itertools.permutations(range(self.num_v), 2))
        self.num_class = copy*n*(n-1)/2 / (k*(k-1)/2)
        assert self.num_class == int(self.num_class)
        self.num_class = int(self.num_class)
        self.nvars = self.num_class*self.num_v
        self.edgemap = dict()
        self.vertexmap = dict()
        self.solver = minisolvers.MinicardSolver()

        # build a vertex map and an edge map (for mapping vertices and edges to their variables)
        i = 1
        for c in range(self.num_class):
            for v in range(self.num_v):
                self.vertexmap[(c, v)] = i
                self.solver.new_var()
                i += 1
        for c in range(self.num_class):
            for (v1,v2) in self.e_all:
                self.edgemap[(c,v1,v2)] = i
                self.solver.new_var(dvar=False)
                i += 1

    def vertices_edges(self):
        for c in range(self.num_class):
            for (u, v) in self.e_all:
                self.solver.add_clause([-self.getvertexvar(c, u), -self.getvertexvar(c, v), self.getedgevar(c, u, v)])
                self.solver.add_clause([self.getvertexvar(c, u), -self.getedgevar(c, u, v)])
                self.solver.add_clause([self.getvertexvar(c, v), -self.getedgevar(c, u, v)])

    def getedgevar(self, c,v1,v2):
        assert v1 != v2
        return self.edgemap[(c,v1,v2)]

    def getvertexvar(self, c,v):
        return self.vertexmap[(c,v)]

    def edge_mutexes(self):
        for (v1, v2) in self.e_all:
            same_edges = []
            for c in range(self.num_class):
                same_edges.append(self.getedgevar(c,v1,v2))
            self.solver.add_atleast(same_edges, self.copy)
            self.solver.add_atmost(same_edges, self.copy)

    def vertex_per_row(self):
        for v in range(self.num_v):
            same_vertices = []
            for c in range(self.num_class):
                same_vertices.append(self.getvertexvar(c,v))
            self.solver.add_atmost(same_vertices, self.r)
            self.solver.add_atleast(same_vertices, self.r)

    def vertex_per_column(self):
        for c in range(self.num_class):
            vertices = []
            for v in range(self.num_v):
                vertices.append(self.getvertexvar(c, v))
            self.solver.add_atmost(vertices, self.num_k)
            self.solver.add_atleast(vertices, self.num_k)

    def lex_leader(self):
        # generating column lex-leader clauses
        for c in range(self.num_class):
            for r in range(self.num_v):
                above = [-self.getvertexvar(c, x) for x in range(r)]
                assumps = above + [self.getvertexvar(c, r)]
                assumps = [-x for x in assumps]
                #print (c,r)
                for p in range(c+1, self.num_class):
                    for q in range(r):
                        self.solver.add_clause(assumps+[-self.getvertexvar(p, q)])
                        #print "---", (p, q), assumps+[-self.getvertexvar(p, q)]

        # generating row lex-leader clauses
        for r in range(self.num_v):
            for c in range(self.num_class):
                before = [-self.getvertexvar(y, r) for y in range(c)]
                assumps = before + [self.getvertexvar(c, r)]
                assumps = [-x for x in assumps]
                #print (c,r)
                for p in range(c):
                    for q in range(r+1, self.num_v):
                        self.solver.add_clause(assumps+[-self.getvertexvar(p, q)])
                        #print "---", (p, q), assumps+[-self.getvertexvar(p, q)]

    def make_formula(self):
        self.edge_mutexes()
        self.vertices_edges()
        self.vertex_per_column()
        self.vertex_per_row()
        with s.time("make lex"):
            self.lex_leader()

    def solve(self):
        return self.solver.solve()

    def block(self):
        self.solver.block_model()


def print_model(lits, num_v, num_class):
    for i in range(num_v):
        row = []
        for j in range(num_class):
            row.append(lits[i+j*(num_v)])
        print("".join([str(x) for x in row]))
    print("")


def at_exit(stats):
    # print stats
    times = stats.get_times()
    counts = stats.get_counts()
    other = stats.get_stats()

    # sort categories by total runtime
    categories = sorted(times, key=times.get)
    maxlen = max(len(x) for x in categories)
    for category in categories:
        sys.stderr.write("%-*s : %8.3f\n" % (maxlen, category, times[category]))


def main():
    num_v = int(sys.argv[1])
    num_k = int(sys.argv[2])
    num_lambda = int(sys.argv[3])
    limit = int(sys.argv[4])
    global s
    s = utils.Statistics()
    d = Decomp(num_v, num_k, num_lambda)
    with s.time("make formula"):
        d.make_formula()
    i = 0
    while True:
        with s.time("solving"):
            if_sat = d.solve()
        if if_sat:
            model = list(d.solver.get_model())
            d.block()
            i += 1
            print(i)
            limit -= 1
            print_model(model[:d.num_v*d.num_class], num_v, d.num_class)
            if limit == 0:
                sys.stderr.write("Result limit reached.\n")
                at_exit(s)
                sys.exit(0)
        else:
            print("unsat")
            break

if __name__ == '__main__':
    main()
