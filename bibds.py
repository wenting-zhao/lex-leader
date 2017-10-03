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
    parser.add_argument('-n', type=int, default=None)
    parser.add_argument('-k', type=int, default=None)
    parser.add_argument('--copy', type=int, default=None)
    parser.add_argument('--option', type=str, default=None)

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="print more verbose output (constraint indexes for MUSes/MCSes) -- repeat the flag for detail about the algorithm's progress)")
    parser.add_argument('-a', '--alltimes', action='store_true',
                        help="print the time for every output")
    parser.add_argument('-s', '--stats', action='store_true',
                        help="print timing statistics to stderr")
    parser.add_argument('-T', '--timeout', type=int, default=None,
                        help="limit the runtime to TIMEOUT seconds")
    parser.add_argument('-l', '--limit', type=int, default=None,
                        help="limit number of subsets output (counting both MCSes and MUSes)")
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
                solver.new_var()
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
    args = parse_args()
    s = utils.Statistics()
    n, k, l = args.n, args.k, args.copy
    lex_option = args.option
    num_class = l*n*(n-1)/2 / (k*(k-1)/2)
    assert num_class == int(num_class)
    num_class = int(num_class)
    global solver
    solver = minisolvers.MinicardSolver()
    lex = lexleader.LexLeader(num_class, n, lex_option)
    with s.time("get_lex"):
        lex_constraints = lex.make_lexleader()
    with s.time("bool2cnf"):
        var2realvar = call_bool2cnf(lex_constraints)
    matrix2var = make_matrixvar(num_class, n)
    make_bibd(n, k, l, num_class, matrix2var, var2realvar)

    count = 0
    while True:
        with s.time("solving"):
            if_sat = solver.solve()
        if if_sat:
            model = list(solver.get_model())
            block_model(model, matrix2var, var2realvar)
            count += 1
            print(count)
            args.limit -= 1
            #print(model[-(n*(n-1)//2)*num_class:])
            if args.verbose == 1:
                print_model(model, n, num_class, matrix2var, var2realvar)

            if args.limit == 0:
                sys.stderr.write("Result limit reached.\n")
                at_exit(s)
                sys.exit(0)
        else:
            print("unsat")
            break

if __name__ == '__main__':
    main()
