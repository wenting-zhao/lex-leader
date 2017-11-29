import os

everything = ("AND", "AND-CSE".upper(), "OR".upper(), "OR-CSE".upper(), "ROR".upper(), "Alpha", "Alpha-m", "Harvey", "Partial-lex", "None")


def main():
    directory = os.fsencode("finalresults")
    allresults = dict()

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".results"):
            pathtofile = os.path.join(directory.decode(), filename)
            with open(pathtofile) as f:
                results = dict()
                this_option = ""
                unsat = False
                for line in f:
                    if line.startswith("[runlim] argv[4]:"):
                        this_option = line.split()[-1]
                    if line.startswith("UNSAT"):
                        unsat = True
                    if line.startswith("[runlim] real:") and unsat:
                        results[this_option] = line.split()[-2]
                        if float(results[this_option]) > 3600:
                            results[this_option] = '3600'
                        unsat = False
            if len(set(results)) > 0:
                allresults[filename.split('.')[0]] = results
    print(','+','.join(everything))
    for instance in allresults.keys():
        result2print = []
        for which in everything:
            result = allresults[instance]
            if which in result:
                result2print.append(result[which])
            else:
                result2print.append(str(3600))
        print(instance.replace(',', '-')+','+','.join(result2print))
main()
