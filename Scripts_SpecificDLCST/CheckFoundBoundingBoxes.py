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
from Preprocessing.OperationImages import *
import argparse



def main(args):
    # ---------- SETTINGS ----------
    nameInputCropImagesRelPath = args.cropimgsdir
    nameInputFullImagesRelPath = args.fullimgsdir
    nameInputReferFilesRelPath = 'CTs_Cropped/'
    nameInputCropImagesFiles   = '*.dcm'
    nameInputFullImagesFiles   = '*.dcm'
    nameInputReferFiles        = '*.dcm'
    nameBoundingBoxes          = 'found_boundBoxes_original.npy'
    # ---------- SETTINGS ----------


    workDirsManager     = WorkDirsManager(args.datadir)
    InputCropImagesPath = workDirsManager.getNameExistPath(nameInputCropImagesRelPath)
    InputFullImagesPath = workDirsManager.getNameExistPath(nameInputFullImagesRelPath)
    InputReferFilesPath = workDirsManager.getNameExistPath(nameInputReferFilesRelPath)

    listInputCropImagesFiles = findFilesDirAndCheck(InputCropImagesPath, nameInputCropImagesFiles)
    listInputFullImagesFiles = findFilesDirAndCheck(InputFullImagesPath, nameInputFullImagesFiles)
    listInputReferFiles      = findFilesDirAndCheck(InputReferFilesPath, nameInputReferFiles)

    dict_bounding_boxes = readDictionary(joinpathnames(args.datadir, nameBoundingBoxes))


    names_files_different = []

    for i, (in_cropimage_file, in_fullimage_file) in enumerate(zip(listInputCropImagesFiles, listInputFullImagesFiles)):
        print("\nInput: \'%s\'..." % (basename(in_cropimage_file)))
        print("Input 2: \'%s\'..." % (basename(in_fullimage_file)))

        in_refer_file = findFileWithSamePrefix(basename(in_cropimage_file), listInputReferFiles,
                                               prefix_pattern='vol[0-9][0-9]_')
        print("Reference file: \'%s\'..." % (basename(in_refer_file)))
        bounding_box = dict_bounding_boxes[filenamenoextension(in_refer_file)]


        crop_image_array = FileReader.getImageArray(in_cropimage_file)
        full_image_array = FileReader.getImageArray(in_fullimage_file)

        # 1 step: crop image
        newcropped_image_array = CropImages.compute3D(full_image_array, bounding_box)
        # 2 step: invert image
        newcropped_image_array = FlippingImages.compute(newcropped_image_array, axis=0)

        if (crop_image_array.shape == newcropped_image_array.shape):
            res_voxels_equal = np.array_equal(crop_image_array, newcropped_image_array)

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
    parser.add_argument('--datadir', default=DATADIR)
    parser.add_argument('cropimgsdir', type=str)
    parser.add_argument('fullimgsdir', type=str)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).iteritems():
        print("\'%s\' = %s" %(key, value))

    main(args)
