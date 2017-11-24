import os

everything = ("and", "and-cse", "or", "or-cse", "ror", "alpha", "alpha-m", "harvey", "mylex", "none")


def main():
    directory = os.fsencode("moreresults")
    allresults = dict()

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".results"):
            pathtofile = os.path.join(directory.decode(), filename)
            with open(pathtofile) as f:
                results = dict()
                for line in f:
                    if line.startswith(everything):
                        split = line.split(',')
                        results[split[0]] = split[-1][:-2]
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
