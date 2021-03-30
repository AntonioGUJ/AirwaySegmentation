
from common.constant import *
from common.functionutil import *
from common.workdirmanager import GeneralDirManager
from dataloaders.imagefilereader import ImageFileReader
from imageoperators.imageoperator import CropImage, RescaleImage, CropAndExtendImage, NormaliseImage
from imageoperators.boundingboxes import BoundingBoxes
from imageoperators.maskoperator import MaskOperator
from collections import OrderedDict
import argparse


def check_same_number_files_in_list(list_files_1: List[str], list_files_2: List[str]):
    if (len(list_files_1) != len(list_files_2)):
        message = 'num files in two lists not equal: \'%s\' != \'%s\'...' %(len(list_files_1), len(list_files_2))
        catch_error_exception(message)

def check_same_size_images(in_image_1: np.ndarray, in_image_2: np.ndarray) -> bool:
    if in_image_1.shape != in_image_2.shape:
        message = "Images have different size: \'%s\' != \'%s\'. Skip these data..." %(str(in_image_1.shape), str(in_image_2.shape))
        catch_warning_exception(message)
        return True
    else:
        return False

def group_filenames_in_list_with_same_prefix(list_input_files: List[str]) -> List[List[str]]:
    pattern_prefix = 'Suj[0-9][0-9]-[a-z]+_'
    list_unique_prefixs_filenames = []
    for ifilename in list_input_files:
        prefix_filename = get_substring_filename(ifilename, pattern_prefix)
        if prefix_filename not in list_unique_prefixs_filenames:
            list_unique_prefixs_filenames.append(prefix_filename)

    list_groups_input_files_all = []
    for iprefix_filename in list_unique_prefixs_filenames:
        list_group_files_this = [ifilename for ifilename in list_input_files if iprefix_filename in ifilename]
        list_groups_input_files_all.append(list_group_files_this)

    return list_groups_input_files_all



def main(args):
    # ---------- SETTINGS ----------
    name_template_output_images_files = 'images_proc-%0.2i.nii.gz'
    name_template_output_labels_files = 'labels_proc-%0.2i.nii.gz'
    name_template_output_extra_labels_files = 'cenlines_proc-%0.2i.nii.gz'
    # ---------- SETTINGS ----------


    workdir_manager         = GeneralDirManager(args.datadir)
    input_images_path       = workdir_manager.get_pathdir_exist(args.name_input_images_relpath)
    in_reference_files_path = workdir_manager.get_pathdir_exist(args.name_input_reference_files_relpath)
    output_images_path      = workdir_manager.get_pathdir_new(args.name_output_images_relpath)
    out_reference_keys_file = workdir_manager.get_pathfile_update(args.name_output_reference_keys_file)
    list_input_images_files = list_files_dir(input_images_path)
    list_in_reference_files = list_files_dir(in_reference_files_path)

    if args.is_prepare_many_images_per_label:
        list_groups_extra_images_files_all = group_filenames_in_list_with_same_prefix(list_input_images_files)
        list_input_images_files = []
        for list_group_files_this in list_groups_extra_images_files_all[1:]:
            check_same_number_files_in_list(list_groups_extra_images_files_all[0], list_group_files_this)
        for list_group_files_this in list_groups_extra_images_files_all:
            list_input_images_files.append(list_group_files_this[0])
            list_group_files_this.pop(0)

    if (args.is_prepare_labels):
        input_labels_path       = workdir_manager.get_pathdir_exist(args.name_input_labels_relpath)
        output_labels_path      = workdir_manager.get_pathdir_new(args.name_output_labels_relpath)
        list_input_labels_files = list_files_dir(input_labels_path)
        check_same_number_files_in_list(list_input_images_files, list_input_labels_files)

    if (args.is_mask_region_interest):
        input_RoImasks_path       = workdir_manager.get_pathdir_exist(args.name_input_RoImasks_relpath)
        list_input_RoImasks_files = list_files_dir(input_RoImasks_path)
        check_same_number_files_in_list(list_input_images_files, list_input_RoImasks_files)

    if (args.is_input_extra_labels):
        input_extra_labels_path       = workdir_manager.get_pathdir_exist(args.name_input_extra_labels_relpath)
        output_extra_labels_path      = workdir_manager.get_pathdir_new  (args.name_output_extra_labels_relpath)
        list_input_extra_labels_files = list_files_dir(input_extra_labels_path)
        check_same_number_files_in_list(list_input_images_files, list_input_extra_labels_files)

    if (args.is_merge_two_images_as_channels):
        input_extra_images_path       = workdir_manager.get_pathdir_exist(args.name_input_extra_images_relpath)
        list_input_extra_images_files = list_files_dir(input_extra_images_path)
        check_same_number_files_in_list(list_input_images_files, list_input_extra_images_files)

    if (args.is_crop_images):
        input_crop_bounding_boxes_file = workdir_manager.get_pathfile_exist(args.name_crop_bounding_boxes_file)
        indict_crop_bounding_boxes     = read_dictionary(input_crop_bounding_boxes_file)

    if args.is_prepare_many_images_per_label:
        is_output_multiple_files_per_image = True
        name_template_output_images_files = 'images_proc-%0.2i_aug-%0.2i.nii.gz'
        is_output_multiple_files_per_label = False
    else:
        is_output_multiple_files_per_image = False
        is_output_multiple_files_per_label = False



    outdict_reference_keys = OrderedDict()

    for ifile, in_image_file in enumerate(list_input_images_files):
        print("\nInput: \'%s\'..." % (basename(in_image_file)))

        inout_image = ImageFileReader.get_image(in_image_file)
        print("Original dims : \'%s\'..." % (str(inout_image.shape)))

        list_inout_data = [inout_image]
        list_type_inout_data = ['image']


        # *******************************************************************************
        if (args.is_merge_two_images_as_channels):
            in_extra_image_file = list_input_extra_images_files[ifile]
            print("And extra image: \'%s\'... Merge as additional channel to the input image..." % (basename(in_extra_image_file)))

            in_extraimage = ImageFileReader.get_image(in_extra_image_file)
            if check_same_size_images(in_extraimage, inout_image):
                message = "FATAL ERROR"
                catch_error_exception(message)

            inout_image = np.stack((inout_image, in_extraimage), axis=-1)


        if (args.is_prepare_many_images_per_label):
            in_list_group_extra_images_files = list_groups_extra_images_files_all[ifile]
            num_extra_images_files = len(in_list_group_extra_images_files)
            print("And \'%s\' extra input images:..." %(num_extra_images_files))

            for i, in_extra_image_file in enumerate(in_list_group_extra_images_files):
                print("\'%s\': \'%s\'..." % (i+1, basename(in_extra_image_file)))

                inout_extra_image = ImageFileReader.get_image(in_extra_image_file)
                list_inout_data.append(inout_extra_image)
                list_type_inout_data.append('image')

                if check_same_size_images(inout_extra_image, inout_image):
                    continue
        # *******************************************************************************


        # *******************************************************************************
        if (args.is_prepare_labels):
            in_label_file = list_input_labels_files[ifile]
            print("And Labels: \'%s\'..." % (basename(in_label_file)))

            inout_label = ImageFileReader.get_image(in_label_file)
            if (args.is_binary_train_masks):
                print("Convert masks to binary (0, 1)...")
                inout_label = MaskOperator.binarise(inout_label)

            list_inout_data.append(inout_label)
            list_type_inout_data.append('label')

            if check_same_size_images(inout_label, inout_image):
                continue


        if (args.is_mask_region_interest):
            in_roimask_file = list_input_RoImasks_files[ifile]
            print("And ROI Mask for labels: \'%s\'..." % (basename(in_roimask_file)))

            in_roimask = ImageFileReader.get_image(in_roimask_file)
            in_roimask = MaskOperator.binarise(in_roimask)
            list_inout_data.append(in_roimask)
            list_type_inout_data.append('roimask')

            if check_same_size_images(in_roimask, inout_image):
                continue


        if (args.is_input_extra_labels):
            in_extra_label_file = list_input_extra_labels_files[ifile]
            print("And extra labels: \'%s\'..." % (basename(in_extra_label_file)))

            inout_extra_label = ImageFileReader.get_image(in_extra_label_file)
            inout_extra_label = MaskOperator.binarise(inout_extra_label)
            list_inout_data.append(inout_extra_label)
            list_type_inout_data.append('label')

            if check_same_size_images(inout_extra_label, inout_image):
                continue
        # *******************************************************************************


        # *******************************************************************************
        if (args.is_normalize_data):
            for j, (in_data, type_in_data) in enumerate(zip(list_inout_data, list_type_inout_data)):
                if (type_in_data == 'image') or \
                    (type_in_data == 'label' and not args.is_binary_train_masks):
                    print('Normalize input data \'%s\' of type \'%s\'...' % (j, type_in_data))
                    out_data = NormaliseImage.compute(in_data)
                    list_inout_data[j] = out_data
            # endfor
        # *******************************************************************************


        # *******************************************************************************
        if (args.is_mask_region_interest):
            index_roimask = list_type_inout_data.find('roimask')

            for j, (in_data, type_in_data) in enumerate(zip(list_inout_data, list_type_inout_data)):
                if (type_in_data == 'label'):
                    print('Mask input data \'%s\' of type \'%s\' to ROI mask...' % (j, type_in_data))
                    out_data = MaskOperator.mask_image_exclude_regions(in_data, list_inout_data[index_roimask])
                    list_inout_data[j] = out_data
            # endfor

            # remove the ROI mask from the list of processing data
            list_type_inout_data.pop(index_roimask)
            list_inout_data.pop(index_roimask)
        # *******************************************************************************


        # *******************************************************************************
        if (args.is_crop_images):
            in_reference_key = list_in_reference_files[ifile]
            in_crop_bounding_box = indict_crop_bounding_boxes[basename_filenoext(in_reference_key)]

            for j, in_data in enumerate(list_inout_data):
                print('Crop input Image \'%s\' to bounding-box: \'%s\'...' % (j, str(in_crop_bounding_box)))
                out_data = CropImage.compute(in_data, in_crop_bounding_box)
                list_inout_data[j] = out_data
            # endfor

            print("Final dims: %s..." % (str(list_inout_data[0].shape)))
        # *******************************************************************************


        # # *******************************************************************************
        # if args.is_prepare_data_stack_images:
        #     print("Prepare data as stack images: roll axis to place the images index as first dimension...")
        #     for j, (in_data, type_in_data) in enumerate(zip(list_inout_data, list_type_inout_data)):
        #         out_data = np.rollaxis(in_data, 2, start=0)
        #         list_inout_data[j] = out_data
        #     # endfor
        #
        #     print("Final dims: %s..." % (str(list_inout_data[0].shape)))
        # # *******************************************************************************


        # Output processed images
        # *******************************************************************************
        if (args.is_prepare_many_images_per_label):
            num_output_files_per_image = num_extra_images_files + 1
            num_output_files_per_label = 1
        else:
            num_output_files_per_image = 1
            num_output_files_per_label = 1

        icount = 0
        for isubfile in range(num_output_files_per_image):
            if list_type_inout_data[icount] != 'image':
                message = 'Expected to output an image, but found data of type %s' %(list_type_inout_data[icount])
                catch_error_exception(message)

            if is_output_multiple_files_per_image:
                output_image_file = join_path_names(output_images_path, name_template_output_images_files % (ifile+1, isubfile+1))
            else:
                output_image_file = join_path_names(output_images_path, name_template_output_images_files % (ifile+1))
            print("Output \'%s\' image, of type \'%s\': \'%s\'..." % (icount+1, list_type_inout_data[icount], basename(output_image_file)))

            ImageFileReader.write_image(output_image_file, list_inout_data[icount])
            icount += 1

            if (args.is_prepare_many_images_per_label) and (isubfile > 0):
                in_image_file = list_groups_extra_images_files_all[ifile][isubfile-1]

            outdict_reference_keys[basename_filenoext(output_image_file)] = basename(in_image_file)
        # endfor

        for isubfile in range(num_output_files_per_label):
            if (args.is_prepare_labels):
                if list_type_inout_data[icount] != 'label':
                    message = 'Expected to output an image, but found data of type %s' % (list_type_inout_data[icount])
                    catch_error_exception(message)

                if is_output_multiple_files_per_label:
                    output_label_file = join_path_names(output_labels_path, name_template_output_labels_files % (ifile+1, isubfile+1))
                else:
                    output_label_file = join_path_names(output_labels_path, name_template_output_labels_files % (ifile+1))
                print("Output \'%s\' label, of type \'%s\': \'%s\'..." % (icount+1, list_type_inout_data[icount], basename(output_label_file)))

                ImageFileReader.write_image(output_label_file, list_inout_data[icount])
                icount += 1

            if (args.is_input_extra_labels):
                if list_type_inout_data[icount] != 'label':
                    message = 'Expected to output an image, but found data of type %s' % (list_type_inout_data[icount])
                    catch_error_exception(message)

                if is_output_multiple_files_per_label:
                    output_extra_label_file = join_path_names(output_labels_path, name_template_output_labels_files % (ifile+1, isubfile+1))
                else:
                    output_extra_label_file = join_path_names(output_labels_path, name_template_output_labels_files % (ifile+1))
                print("Output \'%s\' extra label, of type \'%s\': \'%s\'..." % (icount+1, list_type_inout_data[icount], basename(output_extra_label_file)))

                ImageFileReader.write_image(output_extra_label_file, list_inout_data[icount])
                icount += 1
        # endfor
        # *******************************************************************************
    # endfor

    # Save reference keys for processed data
    save_dictionary(out_reference_keys_file, outdict_reference_keys)
    save_dictionary_csv(out_reference_keys_file.replace('.npy', '.csv'), outdict_reference_keys)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str, default=DATADIR)
    parser.add_argument('--name_input_images_relpath', type=str, default=NAME_RAW_IMAGES_RELPATH)
    parser.add_argument('--name_input_labels_relpath', type=str, default=NAME_RAW_LABELS_RELPATH)
    parser.add_argument('--name_input_RoImasks_relpath', type=str, default=NAME_RAW_ROIMASKS_RELPATH)
    parser.add_argument('--name_input_reference_files_relpath', type=str, default=NAME_REFERENCE_FILES_RELPATH)
    parser.add_argument('--name_input_extra_labels_relpath', type=str, default=NAME_RAW_EXTRALABELS_RELPATH)
    parser.add_argument('--name_output_images_relpath', type=str, default=NAME_PROC_IMAGES_RELPATH)
    parser.add_argument('--name_output_labels_relpath', type=str, default=NAME_PROC_LABELS_RELPATH)
    parser.add_argument('--name_output_extra_labels_relpath', type=str, default=NAME_PROC_EXTRALABELS_RELPATH)
    parser.add_argument('--name_output_reference_keys_file', type=str, default=NAME_REFERENCE_KEYS_PROCIMAGE_FILE)
    parser.add_argument('--is_prepare_labels', type=str2bool, default=True)
    parser.add_argument('--is_input_extra_labels', type=str2bool, default=False)
    parser.add_argument('--is_binary_train_masks', type=str2bool, default=IS_BINARY_TRAIN_MASKS)
    parser.add_argument('--is_mask_region_interest', type=str2bool, default=IS_MASK_REGION_INTEREST)
    parser.add_argument('--is_normalize_data', type=str2bool, default=IS_NORMALIZE_DATA)
    parser.add_argument('--is_crop_images', type=str2bool, default=IS_CROP_IMAGES)
    parser.add_argument('--name_crop_bounding_boxes_file', type=str, default=NAME_CROP_BOUNDINGBOX_FILE)
    parser.add_argument('--is_prepare_many_images_per_label', type=str2bool, default=False)
    parser.add_argument('--is_merge_two_images_as_channels', type=str2bool, default=IS_MERGE_TWO_IMAGES_AS_CHANNELS)
    parser.add_argument('--name_input_extra_images_relpath', type=str, default=NAME_RAW_EXTRAIMAGES_RELPATH)
    # parser.add_argument('--is_prepare_data_stack_images', type=str2bool, default=False)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in sorted(vars(args).items()):
        print("\'%s\' = %s" %(key, value))

    main(args)
