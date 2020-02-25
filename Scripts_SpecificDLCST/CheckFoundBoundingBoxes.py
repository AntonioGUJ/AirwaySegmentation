#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

from Common.Constants import *
from Common.WorkDirsManager import *
from DataLoaders.FileReaders import *
from OperationImages.OperationImages import *
import argparse



def main(args):
    # ---------- SETTINGS ----------
    nameInputCropImagesRelPath = args.cropimagesdir
    nameInputFullImagesRelPath = args.fullimagesdir
    nameInputReferKeysRelPath  = args.referkeysdir
    nameInputBoundingBoxesFile = 'found_boundingBox_croppedCTinFull.npy'
    prefixPatternInputFiles    = 'vol[0-9][0-9]_*'
    # ---------- SETTINGS ----------


    workDirsManager     = WorkDirsManager(args.datadir)
    InputCropImagesPath = workDirsManager.getNameExistPath(nameInputCropImagesRelPath)
    InputFullImagesPath = workDirsManager.getNameExistPath(nameInputFullImagesRelPath)
    InputReferKeysPath  = workDirsManager.getNameExistPath(nameInputReferKeysRelPath)
    InputBoundBoxesFile = workDirsManager.getNameExistFile(nameInputBoundingBoxesFile)

    listInputCropImagesFiles = findFilesDirAndCheck(InputCropImagesPath)
    listInputFullImagesFiles = findFilesDirAndCheck(InputFullImagesPath)
    listInputReferKeysFiles  = findFilesDirAndCheck(InputReferKeysPath)
    dictInputBoundingBoxes   = readDictionary(InputBoundBoxesFile)


    names_files_different = []

    for i, (in_cropimage_file, in_fullimage_file) in enumerate(zip(listInputCropImagesFiles, listInputFullImagesFiles)):
        print("\nInput: \'%s\'..." % (basename(in_cropimage_file)))
        print("Input 2: \'%s\'..." % (basename(in_fullimage_file)))

        in_referkey_file = findFileWithSamePrefixPattern(basename(in_cropimage_file), listInputReferKeysFiles,
                                                         prefix_pattern=prefixPatternInputFiles)
        print("Reference key: \'%s\'..." % (basename(in_referkey_file)))
        in_bounding_box = dictInputBoundingBoxes[filenamenoextension(in_referkey_file)]


        in_cropimage_array = FileReader.getImageArray(in_cropimage_file)
        in_fullimage_array = FileReader.getImageArray(in_fullimage_file)

        # 1 step: crop image
        new_cropimage_array = CropImages.compute3D(in_fullimage_array, in_bounding_box)
        # 2 step: invert image
        new_cropimage_array = FlippingImages.compute(new_cropimage_array, axis=0)

        if (in_cropimage_array.shape == new_cropimage_array.shape):
            res_voxels_equal = np.array_equal(in_cropimage_array, new_cropimage_array)

            if res_voxels_equal:
                print("GOOD: Images are equal voxelwise...")
            else:
                names_files_different.append(basename(in_cropimage_file))
                message = "ERROR: Images are different..."
                CatchWarningException(message)
        else:
            names_files_different.append(basename(in_cropimage_file))
            message = "ERROR: Images are different..."
            CatchWarningException(message)
    #endfor

    if (len(names_files_different) == 0):
        print("\nGOOD: ALL IMAGE FILES ARE EQUAL...")
    else:
        print("\nERROR: Found \'%s\' files that are different. Names of files: \'%s\'..." %(len(names_files_different),
                                                                                            names_files_different))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str, default=DATADIR)
    parser.add_argument('cropimagesdir', type=str)
    parser.add_argument('fullimagesdir', type=str)
    parser.add_argument('--referkeysdir', type=str, default='CTs_Cropped/')
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).iteritems():
        print("\'%s\' = %s" %(key, value))

    main(args)
