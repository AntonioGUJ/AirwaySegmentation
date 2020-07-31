#
# created by
# Antonio Garcia-Uceda Juarez
# PhD student
# Medical Informatics
#
# created on 09/02/2018
# Last update: 09/02/2018
########################################################################################

from common.exception_manager import *
from dataloaders.imagefilereader import *
from imageoperators.boundingboxes import *
from imageoperators.imageoperator import *
import argparse


def compute_test_range_boundbox(images_full_shape, images_crop_shape, alpha_relax=0.5, z_min_top=0, z_numtest=1):
    test_range_boundbox = np.zeros((3, 2), dtype=np.int)
    y_0 = (1.0 - alpha_relax) * (int(np.float(images_full_shape[1]) / 2) - int(np.ceil(np.float(images_crop_shape[1]) / 2)))
    x_0 = (1.0 - alpha_relax) * (int(np.float(images_full_shape[2]) / 2) - int(np.ceil(np.float(images_crop_shape[2]) / 2)))
    z_m = images_full_shape[0] - z_min_top
    z_0 = z_m - images_crop_shape[0] - (z_numtest-1)
    test_range_boundbox[0, 0] = z_0
    test_range_boundbox[0, 1] = z_m
    test_range_boundbox[1, 0] = y_0
    test_range_boundbox[1, 1] = images_full_shape[1] - y_0
    test_range_boundbox[2, 0] = x_0
    test_range_boundbox[2, 1] = images_full_shape[2] - x_0
    return test_range_boundbox


def compute_num_tests_boundbox(test_range_boundbox_shape, images_crop_shape):
    num_test_boundbox = test_range_boundbox_shape - images_crop_shape + [1, 1, 1]
    num_tests_total = num_test_boundbox[0] * num_test_boundbox[1] * num_test_boundbox[2]
    return (num_test_boundbox, num_tests_total)


def get_limits_test_boundbox(test_range_boundbox, size_crop_image, index, option='start_begin'):
    if (option=='start_begin'):
        x0 = test_range_boundbox[0] + index
        xm = x0 + size_crop_image
    elif (option=='start_end'):
        xm = test_range_boundbox[1] - index
        x0 = xm - size_crop_image
    else:
        return None
    return (x0, xm)



def main(args):
    # ---------- SETTINGS ----------
    #test_range_boundbox = ((16, 352), (109, 433), (45, 460))
    _eps = 1.0e-06
    _alpha_relax = 0.6
    _z_min_top = 15
    _z_numtest = 10
    nameTempOutResFile   = 'temp_found_boundingBox_vol16.csv'
    # ---------- SETTINGS ----------


    listInputFullImagesFiles = list_files_dir(args.fullimagesdir)
    listInputCropImagesFiles = list_files_dir(args.cropimagesdir)

    nameTempOutResFile = join_path_names(nameTempOutResFile)
    fout = open(nameTempOutResFile, 'w')


    dict_found_boundingBoxes = {}

    for in_full_image_file, in_crop_image_file in zip(listInputFullImagesFiles, listInputCropImagesFiles):
        print("\nInput: \'%s\'..." %(basename(in_full_image_file)))
        print("And: \'%s\'..." %(basename(in_crop_image_file)))

        in_fullimage_array = ImageFileReader.get_image(in_full_image_file)
        in_cropimage_array = ImageFileReader.get_image(in_crop_image_file)
        in_cropimage_array = FlipImage.compute(in_cropimage_array, axis=0)

        full_image_shape = np.array(in_fullimage_array.shape)
        crop_image_shape = np.array(in_cropimage_array.shape)
        test_range_boundbox = compute_test_range_boundbox(full_image_shape,
                                                          crop_image_shape,
                                                          alpha_relax=_alpha_relax,
                                                          z_min_top=_z_min_top,
                                                          z_numtest=_z_numtest)

        test_range_boundbox_shape = BoundingBoxes.get_size_bounding_box(test_range_boundbox)
        if (test_range_boundbox_shape < in_cropimage_array.shape):
            message = 'size test range of Bounding Boxes than cropped Image: \'%s\' < \'%s\'...' %(test_range_boundbox_shape,
                                                                                                   in_cropimage_array.shape)
            catch_error_exception(message)
        else:
            test_range_boundbox_shape = np.array(test_range_boundbox_shape)

        (num_test_boundbox, num_tests_total) = compute_num_tests_boundbox(test_range_boundbox_shape,
                                                                          in_cropimage_array)
        print("size full image: \'%s\'..." %(full_image_shape))
        print("size cropped image: \'%s\'..." %(crop_image_shape))
        print("test range bounding boxes: \'%s\'..." %(test_range_boundbox))
        print("size test range bounding boxes: \'%s\'..." %(test_range_boundbox_shape))
        print("num test bounding boxes: \'%s\'..." %(num_test_boundbox))
        print("num tests total: \'%s\'..." %(num_tests_total))


        flag_found_boundbox = False
        min_sum_test_res = 1.0e+10
        found_boundbox = None
        counter = 1
        for k in range(num_test_boundbox[0]):
            (z0, zm) = get_limits_test_boundbox(test_range_boundbox[0], crop_image_shape[0], k, option='start_end')
            for j in range(num_test_boundbox[1]):
                (y0, ym) = get_limits_test_boundbox(test_range_boundbox[1], crop_image_shape[1], j, option='start_begin')
                for i in range(num_test_boundbox[2]):
                    (x0, xm) = get_limits_test_boundbox(test_range_boundbox[2], crop_image_shape[2], i, option='start_begin')
                    #print("test \"%s\" of \"%s\"..." %(counter, num_tests_total))
                    #counter = counter + 1
                    test_bounding_box = ((z0,zm),(y0,ym),(x0,xm))
                    #print("test bounding box: %s..." %(test_bounding_box))
                    test_res_matrix = in_fullimage_array[test_bounding_box[0][0]:test_bounding_box[0][1],
                                                       test_bounding_box[1][0]:test_bounding_box[1][1],
                                                       test_bounding_box[2][0]:test_bounding_box[2][1]] - in_cropimage_array
                    sum_test_res = np.abs(np.sum(test_res_matrix))
                    if (sum_test_res <_eps):
                        flag_found_boundbox = True
                        min_sum_test_res = 0.0
                        found_boundbox = test_bounding_box
                        break
                    elif (sum_test_res < min_sum_test_res):
                        min_sum_test_res = sum_test_res
                        found_boundbox = test_bounding_box
                if (flag_found_boundbox):
                    break
            if (flag_found_boundbox):
                break
                #endfor
            #endfor
        #endfor

        if (flag_found_boundbox):
            print("SUCESS: found perfect bounding-box: \'%s\', with null error: \'%s\'..." % (str(found_boundbox), sum_test_res))
            rootimagescropname = basename_file_noext(in_crop_image_file)
            dict_found_boundingBoxes[rootimagescropname] = found_boundbox
            message = "%s,\"%s\"\n" %(rootimagescropname, str(found_boundbox))
            fout.write(message)
        else:
            print("ERROR: not found perfect bounding-box. Closest found is: \'%s\', with error: \'%s\'..." % (str(found_boundbox), min_sum_test_res))
            rootimagescropname = basename_file_noext(in_crop_image_file)
            dict_found_boundingBoxes[rootimagescropname] = found_boundbox
            message = "%s,\"%s\" ...NOT PERFECT...\n" % (rootimagescropname, str(found_boundbox))
            fout.write(message)
    #endfor


    # Save dictionary in file
    save_dictionary(args.outputBoundBoxesFile, dict_found_boundingBoxes)
    save_dictionary_csv(args.outputBoundBoxesFile.replace('.npy', '.csv'), dict_found_boundingBoxes)

    fout.close()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('cropimagesdir', type=str)
    parser.add_argument('fullimagesdir', type=str)
    parser.add_argument('--outputBoundBoxesFile', type=str, default='found_boundingBox_croppedCTinFull.npy')
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).items():
        print("\'%s\' = %s" %(key, value))

    main(args)