#!/usr/bin/env python3

import sys
import lexleader
import os
import itertools
import utils
import argparse
from subprocess import Popen, PIPE
from pyminisolvers import minisolvers


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instance', type=str, default=None)
    parser.add_argument('--option', type=str, default=None)

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="print the actual designs")
    parser.add_argument('-s', '--stats', action='store_true',
                        help="print timing statistics to stderr")
    parser.add_argument('-l', '--limit', type=int, default=None,
                        help="limit number of design outputs")
    args = parser.parse_args()
    return args


def parse_dimacs(f):
    i = 0
    for line in f:
        if line.startswith('p'):
            tokens = line.split()
            nvars = int(tokens[2])
            nclauses = int(tokens[3])

            while solver.nvars() < nvars:
                solver.new_var(polarity=False)
            continue  # skip parsing the first line
        if line == "":
            continue  # skip parsing the last line
        lits = line.split()

        clause = [int(x) for x in lits[:-1]]
        solver.add_clause(clause)

        i += 1
    assert i == nclauses


def call_bool2cnf(formula):
    pathtofile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bool2cnf')
    p = Popen([pathtofile, '-s'], stdout=PIPE, stdin=PIPE)
    stdout, _ = p.communicate(input=formula.encode('utf-8'))
    try:
        tmp_map, cnf = stdout.decode("utf-8").split('p')
        #print(tmp_map, cnf)
    except Exception as e:
        raise e
    var2realvar = parse_varmap(tmp_map.split('\n'))
    parse_dimacs(('p'+cnf).split('\n'))
    return var2realvar


def parse_varmap(inlist):
    var2realvar = dict()
    for each in inlist:
        if each.startswith('c'):
            after_split = each.split()
            var2realvar[int(after_split[-2][1:])] = int(after_split[-1])
    #print(var2realvar)
    return var2realvar


def make_bibd(n, k, l, num_class, matrix2var, var2realvar):
    e_all = list(itertools.permutations(range(n), 2))
    r = l*(n-1)/(k-1)
    assert r == int(r)
    r = int(r)
    edgemap = dict()
    i = solver.nvars()
    for c in range(num_class):
        for (v1,v2) in e_all:
            i += 1
            edgemap[(c,v1,v2)] = i
            solver.new_var(dvar=False)

    for c in range(num_class):
        for (u, v) in e_all:
            solver.add_clause([-var2realvar[matrix2var[(c,v)]], -var2realvar[matrix2var[(c,u)]], edgemap[(c,u,v)]])
            solver.add_clause([var2realvar[matrix2var[(c,u)]], -edgemap[(c,u,v)]])
            solver.add_clause([var2realvar[matrix2var[(c,v)]], -edgemap[(c,u,v)]])

    for (v1, v2) in e_all:
        same_edges = []
        for c in range(num_class):
            same_edges.append(edgemap[(c,v1,v2)])
        solver.add_atleast(same_edges, l)
        solver.add_atmost(same_edges, l)

    for v in range(n):
        same_vertices = []
        for c in range(num_class):
            same_vertices.append(var2realvar[matrix2var[(c,v)]])
        solver.add_atmost(same_vertices, r)
        solver.add_atleast(same_vertices, r)

    for c in range(num_class):
        vertices = []
        for v in range(n):
            vertices.append(var2realvar[matrix2var[(c,v)]])
        solver.add_atmost(vertices, k)
        solver.add_atleast(vertices, k)


def make_mylex(num_class, num_v, matrix2var, full=False):
    # generating column lex-leader clauses
    for c in range(num_class-1, 0, -1):
        for r in range(num_v):
            above = [-matrix2var[(c, x)] for x in range(r)]
            assumps = above + [matrix2var[(c, r)]]
            assumps = [-x for x in assumps]
            if full:
                custom_range = range(c+1, self.num_class)
            else:
                custom_range = [c-1]
            for p in custom_range:
                for q in range(r):
                    solver.add_clause(assumps+[-matrix2var[(p, q)]])

    # generating row lex-leader clauses
    for r in range(num_v-1, 0, -1):
        for c in range(num_class):
            before = [-matrix2var[(y, r)] for y in range(c)]
            assumps = before + [matrix2var[(c, r)]]
            assumps = [-x for x in assumps]
            for p in range(c):
                if full:
                    custom_range = range(r+1, num_v)
                else:
                    custom_range = [r-1]
                for q in custom_range:
                    solver.add_clause(assumps+[-matrix2var[(p, q)]])


def make_matrixvar(num_c, num_r):
    matrix2var = dict()
    i = 1
    for c in range(num_c):
        for r in range(num_r):
            matrix2var[(c, r)] = i
            i += 1
    return matrix2var


def print_model(lits, num_v, num_class, matrix2var, var2realvar):
    for i in range(num_v):
        row = []
        for j in range(num_class):
            row.append(lits[var2realvar[matrix2var[(j,i)]]-1])
        print("".join([str(x) for x in row]))
    print("")


def block_model(model, matrix2var, var2realvar):
    lits = []
    for i in matrix2var.values():
        if model[var2realvar[i]-1] == 1:
            lits.append(-var2realvar[i])
        else:
            lits.append(var2realvar[i])
    solver.add_clause(lits)


def at_exit(stats_from, option):
    stats_to = dict()
    times = stats_from.get_times()
    categories = sorted(times, key=times.get)
    for category in categories:
        stats_to[category] = times[category]
    for key, value in solver.get_stats().items():
        stats_to[key] = value
    stats_to['clauses'] = solver.nclauses()
    keys = sorted(stats_to.keys())
    print(keys)
    print(option+','+','.join(str(round(stats_to[k],3)) for k in keys))


def main():
    args = parse_args()
    s = utils.Statistics()
    n, k, l = [int(i) for i in args.instance.split(',')]
    if args.limit is None:
        args.limit = float("inf")
    lex_option = args.option
    num_class = l*n*(n-1)/2 / (k*(k-1)/2)
    assert num_class == int(num_class)
    num_class = int(num_class)
    global solver
    solver = minisolvers.MinicardSolver()
    matrix2var = make_matrixvar(num_class, n)

    if lex_option == "none" or lex_option == "mylex":
        # for not-using-any-lex option, an identity dict is created
        # to avoid "var2realvar" not defined error.
        var2realvar = {i: i for i in range(1, num_class*n+1)}

        # then make vertex vars
        while solver.nvars() < num_class*n:
            solver.new_var()

        if lex_option == "mylex":
            make_mylex(num_class, n, matrix2var)

        # for timing purpose...
        with s.time("get_lex"):
            pass
        with s.time("bool2cnf"):
            pass

    else:
        lex = lexleader.LexLeader(num_class, n, lex_option)
        with s.time("get_lex"):
            lex_constraints = lex.make_lexleader()
        with s.time("bool2cnf"):
            var2realvar = call_bool2cnf(lex_constraints)

    make_bibd(n, k, l, num_class, matrix2var, var2realvar)

    count = 0
    while True:
        with s.time("solving"):
            if_sat = solver.solve()
        if if_sat:
            model = list(solver.get_model())
            block_model(model, matrix2var, var2realvar)
            count += 1
            args.limit -= 1
            if args.verbose == 1:
                print_model(model, n, num_class, matrix2var, var2realvar)

            if args.limit == 0:
                sys.stderr.write("Result limit reached.\n")
                if args.stats:
                    at_exit(s, lex_option)
                sys.exit(0)
        else:
            if args.stats:
                at_exit(s, lex_option)
            sys.exit(0)

if __name__ == '__main__':
    main()
