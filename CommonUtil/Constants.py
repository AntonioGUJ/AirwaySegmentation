#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

import numpy as np
np.random.seed(2017)


DATADIR = '/home/antonio/testSegmentation/Data/LUVAR/'
BASEDIR = '/home/antonio/testSegmentation/Tests_LUVAR_LUNGS/'


# ******************** INPUT IMAGES PARAMETERS ********************
# MUST BE MULTIPLES OF 16
IMAGES_DEPTHZ = 32
#IMAGES_HEIGHT = 352
IMAGES_HEIGHT = 256
#IMAGES_WIDTH  = 240
IMAGES_WIDTH  = 256

IMAGES_DIMS_X_Y   = (IMAGES_HEIGHT, IMAGES_WIDTH)
IMAGES_DIMS_Z_X_Y = (IMAGES_DEPTHZ, IMAGES_HEIGHT, IMAGES_WIDTH)

FORMATIMAGEDATA   = np.int16
FORMATMASKDATA    = np.int8
FORMATPREDICTDATA = np.float32

SHUFFLEIMAGES   = True
NORMALIZEDATA   = False
FORMATINOUTDATA = 'numpy'
# ******************** INPUT IMAGES PARAMETERS ********************


# ******************** DATA DISTRIBUTION ********************
PROP_TRAINING   = 0.5
PROP_VALIDATION = 0.25
PROP_TESTING    = 0.25
DISTRIBUTE_RANDOM = False
# ******************** DATA DISTRIBUTION ********************


# ******************** PRE-PROCESSING PARAMETERS ********************
TYPEDATA = 'training'

REDUCESIZEIMAGES = False

SIZEREDUCEDIMAGES = (256, 256)

CROPIMAGES = True

CROPSIZEBOUNDINGBOX = (352, 480)

CONFINEMASKSTOLUNGS = True

CHECKBALANCECLASSES = True

SLIDINGWINDOWIMAGES = True

CREATEIMAGESBATCHES = False

PROP_OVERLAP_Z_X_Y = (0.75, 0.0, 0.0)

SAVEVISUALPROCESSDATA = False
# ******************** PRE-PROCESSING PARAMETERS ********************


# ******************** TRAINING PARAMETERS ********************
NUM_EPOCHS = 1000
BATCH_SIZE = 1
IMODEL     = 'Unet3D_Shallow'
IOPTIMIZER = 'Adam'
#ILOSSFUN   = 'WeightedBinaryCrossEntropy_Masked'
ILOSSFUN   = 'BinaryCrossEntropy'
#IMETRICS   = 'DiceCoefficient_Masked'
IMETRICS   = 'DiceCoefficient'
LEARN_RATE = 1.0e-05

USE_DATAAUGMENTATION = True

USE_RESTARTMODEL = False

EPOCH_RESTART = 40
RESTART_MODELFILE = 'lastEpoch'
# ******************** TRAINING PARAMETERS ********************


# ******************** POST-PROCESSING PARAMETERS ********************
PREDICTION_MODELFILE = 'lastEpoch'

#PREDICTIONACCURACY = 'DiceCoefficient_Masked'
PREDICTIONACCURACY = 'DiceCoefficient'

THRESHOLDOUTIMAGES = False

THRESHOLDVALUE = 0.5

SAVEVISUALPREDICTDATA = False
# ******************** POST-PROCESSING PARAMETERS ********************