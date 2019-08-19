#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

from Common.FunctionsUtil import *
import matplotlib.pyplot as plt
import seaborn as sns
from collections import *
import numpy as np
import argparse



def main(args):

    if args.fromfile:
        if not isExistfile(args.listinputfiles):
            message = "File \'%s\' not found..." %(args.listinputfiles)
            CatchErrorException(message)
        fout = open(args.listinputfiles, 'r')
        list_input_files = [infile.replace('\n','') for infile in fout.readlines()]
        print("\'inputfiles\' = %s" % (list_input_files))
    else:
        list_input_files = [infile.replace('\n','') for infile in args.inputfiles]
    num_data_files = len(list_input_files)

    print("Files to plot (\'%s\')..." %(num_data_files))
    for i, ifile in enumerate(list_input_files):
        print("%s: \'%s\'" %(i+1, ifile))
    #endfor

    #labels = ['model_%i'%(i+1) for i in range(num_data_files)]
    labels = ['UnetLev3', 'UnetLev5', 'UGnnReg', 'UGnnDyn']
    titles = ['Distance False Positives', 'Distance False Negatives']
    names_outfiles = ['figure_resDFP_NEW.eps', 'figure_resDFN_NEW.eps']


    data_fields_files = OrderedDict()
    data_cases_files = OrderedDict()
    fields_names = []
    cases_names = []

    for i in range(num_data_files):
        data_file_this = list_input_files[i]
        raw_data_this_string = np.genfromtxt(data_file_this, dtype=str, delimiter=',')
        raw_data_this_float = np.genfromtxt(data_file_this, dtype=float, delimiter=',')

        fields_names_this = [item.replace('/','') for item in raw_data_this_string[0,1:]]
        cases_names_this = [item.replace('\'','') for item in raw_data_this_string[1:,0]]
        data_this = raw_data_this_float[1:,1:]
        num_fields_this = len(fields_names_this)
        num_cases_this = len(cases_names_this)

        if i==0:
            fields_names = fields_names_this
            cases_names = cases_names_this
            for (i, key) in enumerate(fields_names):
                data_fields_files[key] = []
            for (i, key) in enumerate(cases_names):
                data_cases_files[key] = []
        else:
            if fields_names_this != fields_names:
                message = 'fields found in file \'%s\' do not match those found previously: \'%s\'' %(data_file, fields_names)
                CatchErrorException(message)
            #if cases_names_this != cases_names:
                #message = 'fields found in file \'%s\' do not match those found previously: \'%s\'' %(data_file, cases_names)
                #CatchErrorException(message)

        # store data for fields in dictionary
        for (i, key) in enumerate(fields_names):
            if i==1 or i==2:
                data_this[:, i] = 100*data_this[:,i]
            data_fields_files[key].append(data_this[:,i])
        # store data for cases in dictionary
        for (i, key) in enumerate(cases_names):
            data_cases_files[key].append(data_this[i,:])
    #endfor

    print("Found fields to plot: \'%s\'..." %(', '.join(map(lambda item: '/'+item+'/', fields_names))))
    print("Found cases to plot: \'%s\'..." %(', '.join(map(lambda item: '/'+item+'/', cases_names))))


    for i, (key, data) in enumerate(data_fields_files.iteritems()):
        #plt.boxplot(data, labels=labels)
        sns.boxplot(data=data, palette='Set2', width=0.8)
        sns.swarmplot(data=data, color=".25")
        plt.xticks(plt.xticks()[0], labels, size=15)
        plt.yticks(plt.yticks()[0], size=15)
        plt.title(str(key), size=25)
        plt.show()
        #plt.savefig(names_outfiles[i], format='eps', dpi=1000)
        #plt.close()
    #endfor



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfiles', type=str, nargs='*')
    parser.add_argument('--fromfile', type=bool, default=False)
    parser.add_argument('--listinputfiles', type=str, default='listinputfiles.txt')
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).iteritems():
        print("\'%s\' = %s" %(key, value))

    if args.fromfile and not args.listinputfiles:
        print("ERROR. Input input file name with files to plot...")

    main(args)
