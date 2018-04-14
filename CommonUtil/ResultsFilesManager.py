#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

from CommonUtil.FunctionsUtil import *


class ResultsFilesManager(object):

    nameLossHistoryFile = 'lossHistory.txt'
    nameModelLastEpoch  = 'model_lastEpoch.hdf5'
    nameModelMinLoss    = 'model_minLoss.hdf5'
    nameModelMinValoss  = 'model_minValoss.hdf5'


    def __init__(self, resultsDir):
        self.resultsDir = resultsDir
        if not isExistdir(resultsDir):
            message = "WorkDirsManager: results dir does not exists..."
            CatchErrorException(message)


    def cleanUpResultsDir_EndTests(self):
        # remove all output files except:
        # 1) 'lossHistory.txt'
        # 2) model corresponding to: last epoch, and minimum train and valid loss

        list_outfiles_remove = listfilesDir(self.resultsDir)

        list_outfiles_remove.remove(joinpathnames(self.resultsDir, self.nameLossHistoryFile))

        # Extract info: (epochs, loss, valoss), from the output files
        list_outfiles_epochs = []
        list_outfiles_loss   = []
        list_outfiles_valoss = []
        for file in list_outfiles_remove:
            attributes = basename(file).replace('model_', '').replace('.hdf5', '').split('_')
            list_outfiles_epochs.append(int  (attributes[0]))
            list_outfiles_loss  .append(float(attributes[1]))
            list_outfiles_valoss.append(float(attributes[2]))
        # endfor

        outfile_lastepoch = list_outfiles_remove(list_outfiles_epochs.index(max(list_outfiles_epochs)))
        outfile_minloss   = list_outfiles_remove(list_outfiles_loss  .index(max(list_outfiles_loss)))
        outfile_minvaloss = list_outfiles_remove(list_outfiles_epochs.index(max(list_outfiles_valoss)))

        if outfile_lastepoch in list_outfiles_remove:
            list_outfiles_remove.remove(outfile_lastepoch)
        if outfile_minloss in list_outfiles_remove:
            list_outfiles_remove.remove(outfile_minloss)
        if outfile_minvaloss in list_outfiles_remove:
            list_outfiles_remove.remove(outfile_minvaloss)

        # remove output files
        for file in list_outfiles_remove:
            removefile(file)
        # endfor

        # finally, link to remaining files
        makelink(basename(outfile_lastepoch), joinpathnames(self.resultsDir, self.nameModelLastEpoch))
        makelink(basename(outfile_minloss),   joinpathnames(self.resultsDir, self.nameModelMinLoss  ))
        makelink(basename(outfile_minvaloss), joinpathnames(self.resultsDir, self.nameModelMinValoss))


    def completeLossHistoryRestart(self):

        restart_file_link   = joinpathnames(self.resultsDir, self.nameModelLastEpoch)
        realpath_restartdir = dirnamepathfile(realpathlink(restart_file_link))
        removefile(restart_file_link)

        restart_losshistory_file = open(joinpathnames(realpath_restartdir, self.nameLossHistoryFile), 'r')
        current_losshistory_file = open(joinpathnames(self.resultsDir, self.nameLossHistoryFile), 'r')
        restart_losshistory = restart_losshistory_file.readlines()
        current_losshistory = current_losshistory_file.readlines()
        restart_losshistory_file.close()
        current_losshistory_file.close()

        current_losshistory = restart_losshistory + current_losshistory[1:]
        current_losshistory_file = open(joinpathnames(self.resultsDir, self.nameLossHistoryFile), 'w')
        current_losshistory_file.writelines(current_losshistory)
        current_losshistory_file.close()


    def computeLastEpochInFiles(self):

        list_outfiles_remove = listfilesDir(self.resultsDir)

        list_outfiles_epochs = []
        for file in list_outfiles_remove:
            attributes = basename(file).replace('model_', '').replace('.hdf5', '').split('_')
            list_outfiles_epochs.append(int(attributes[0]))
        # endfor

        return max(list_outfiles_epochs)