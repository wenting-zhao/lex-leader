import os
import sys

everything = ("and", "and-cse", "or", "or-cse", "ror", "alpha", "alpha-m", "harvey", "mylex", "none")
attributes = ['bool2cnf', 'clauses', 'conflicts', 'decisions', 'get_lex', 'propagations', 'rnd_decisions', 'solves', 'solving', 'starts', 'total']


def main():
    which_attribute = sys.argv[1]
    directory = os.fsencode("finalresults")
    allresults = dict()

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".results"):
            pathtofile = os.path.join(directory.decode(), filename)
            this_option = ""
            with open(pathtofile) as f:
                results = dict()
                for line in f:
                    if line.startswith("[runlim] argv[4]:"):
                        this_option = line.split()[-1]
                    if line.startswith(this_option) and this_option != "":
                        results[this_option] = line.split(',')[attributes.index(which_attribute)+1]
                        print(line)
            allresults[filename.split('.')[0]] = results
    print(','+','.join(everything))
    for instance in allresults.keys():
        result2print = []
        for which in everything:
            result = allresults[instance]
            if which in result:
                result2print.append(result[which])
            else:
                result2print.append("")
        print(instance.replace(',', '-')+','+','.join(result2print))
main()
