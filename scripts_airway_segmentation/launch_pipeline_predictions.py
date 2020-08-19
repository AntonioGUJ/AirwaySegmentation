
from common.constant import *
from common.functionutil import *
import subprocess
import traceback
import sys
import argparse


CODEDIR                             = join_path_names(BASEDIR, 'Code/')
SCRIPT_PREDICT_MODEL                = join_path_names(CODEDIR, 'scripts_experiments/predict_model.py')
SCRIPT_POSTPROCESS_PREDICTIONS      = join_path_names(CODEDIR, 'scripts_airway_segmentation/postprocess_predictions.py')
SCRIPT_PROCESS_PREDICT_AIRWAY_TREE  = join_path_names(CODEDIR, 'scripts_airway_segmentation/process_predicted_airway_tree.py')
SCRIPT_CALC_CENTRELINES_FROM_MASK   = join_path_names(CODEDIR, 'scripts_util/apply_operation_images.py')
SCRIPT_CALC_FIRST_CONNREGION_FROM_MASK= join_path_names(CODEDIR, 'scripts_util/apply_operation_images.py')
SCRIPT_COMPUTE_RESULT_METRICS       = join_path_names(CODEDIR, 'scripts_airway_segmentation/compute_result_metrics.py')


def print_call(new_call):
    message = ' '.join(new_call)
    print("*" * 100)
    print("<<< Launch: %s >>>" %(message))
    print("*" * 100 +"\n")

def launch_call(new_call):
    popen_obj = subprocess.Popen(new_call)
    popen_obj.wait()

def create_task_replace_dirs(input_dir, input_dir_to_replace):
    new_call_1 = ['rm', '-r', input_dir]
    new_call_2 = ['mv', input_dir_to_replace, input_dir]
    return [new_call_1, new_call_2]



def main(args):
    # ---------- SETTINGS ----------
    name_tempo_posteriors_relpath    = 'PosteriorsWorkData/'
    name_posteriors_relpath          = 'Posteriors/'
    name_predict_binary_masks_relpath= 'BinaryMasks/'
    name_predict_centrelines_relpath = 'Centrelines/'
    name_predict_reference_keys_file = 'referenceKeys_posteriors.npy'
    name_output_results_metrics_file = 'result_metrics.csv'
    # ---------- SETTINGS ----------


    inputdir = dirname(args.input_model_file)
    in_config_params_file = join_path_names(inputdir, NAME_CONFIG_PARAMS_FILE)

    if not is_exist_file(in_config_params_file):
        message = "Config params file not found: \'%s\'..." % (in_config_params_file)
        catch_error_exception(message)
    else:
        input_args_file = read_dictionary_configparams(in_config_params_file)
    #print("Retrieve BaseDir from file: \'%s\'...\n" % (in_cfgparams_file))
    #basedir = str(input_args_file['basedir'])
    basedir = currentdir()


    # output_basedir = update_dirname(args.output_basedir)
    output_basedir = args.output_basedir
    makedir(output_basedir)

    inout_tempo_posteriors_path      = join_path_names(output_basedir, name_tempo_posteriors_relpath)
    inout_predict_reference_keys_file= join_path_names(output_basedir, name_predict_reference_keys_file)
    output_posteriors_path           = join_path_names(output_basedir, name_posteriors_relpath)
    output_predict_binary_masks_path = join_path_names(output_basedir, name_predict_binary_masks_relpath)
    output_predict_centrelines_path  = join_path_names(output_basedir, name_predict_centrelines_relpath)



    list_calls_all = []

    # 1st: Compute model predictions, and posteriors for testing work data
    new_call = ['python3', SCRIPT_PREDICT_MODEL, args.input_model_file,
                '--basedir', basedir,
                '--is_config_fromfile', in_config_params_file,
                '--name_output_predictions_relpath', inout_tempo_posteriors_path,
                '--name_output_reference_keys_file', inout_predict_reference_keys_file,
                '--testing_datadir', args.testing_datadir]
    list_calls_all.append(new_call)


    # 2nd: Compute post-processed posteriors from work predictions
    new_call = ['python3', SCRIPT_POSTPROCESS_PREDICTIONS,
                '--basedir', basedir,
                '--name_input_predictions_relpath', inout_tempo_posteriors_path,
                '--name_input_reference_keys_file', inout_predict_reference_keys_file,
                '--name_output_posteriors_relpath', output_posteriors_path,
                '--is_mask_region_interest', str(IS_MASK_REGION_INTEREST),
                '--is_crop_images', str(IS_CROP_IMAGES),
                '--is_rescale_images', str(IS_RESCALE_IMAGES)]
    list_calls_all.append(new_call)


    # 3rd: Compute the predicted binary masks from the posteriors
    new_call = ['python3', SCRIPT_PROCESS_PREDICT_AIRWAY_TREE,
                '--basedir', basedir,
                '--name_input_posteriors_relpath', output_posteriors_path,
                '--name_output_binary_masks_relpath', output_predict_binary_masks_path,
                '--post_threshold_values', ' '.join([str(el) for el in args.post_thresholds_values]),
                '--is_attach_coarse_airways', 'True']
    list_calls_all.append(new_call)


    if args.is_connected_masks:
        output_tempo_predict_binary_masks_path = set_dirname_suffix(output_predict_binary_masks_path, 'Tempo')

        # Compute the first connected component from the predicted binary masks
        new_call = ['python3', SCRIPT_CALC_FIRST_CONNREGION_FROM_MASK, output_predict_binary_masks_path, output_tempo_predict_binary_masks_path,
                    '--type', 'firstconreg']
        list_calls_all.append(new_call)

        new_sublist_calls = create_task_replace_dirs(output_predict_binary_masks_path, output_tempo_predict_binary_masks_path)
        list_calls_all += new_sublist_calls


    # 4th: Compute centrelines by thinning the binary masks
    new_call = ['python3', SCRIPT_CALC_CENTRELINES_FROM_MASK, output_predict_binary_masks_path, output_predict_centrelines_path,
                '--type', 'thinning']
    list_calls_all.append(new_call)


    # 5th: Compute testing metrics from predicted binary masks and centrelines
    new_call = ['python3', SCRIPT_COMPUTE_RESULT_METRICS, output_predict_binary_masks_path,
                '--basedir', basedir,
                '--input_centrelines_dir', output_predict_centrelines_path,
                '--output_file', name_output_results_metrics_file,
                #'--list_type_metrics_result', ' '.join([el for el in args.list_type_metrics_result]),
                '--is_remove_trachea_calc_metrics', str(IS_REMOVE_TRACHEA_CALC_METRICS)]
    list_calls_all.append(new_call)


    # Remove temporary data for posteriors not needed
    new_call = ['rm', '-r', inout_tempo_posteriors_path]
    list_calls_all.append(new_call)
    new_call = ['rm', inout_predict_reference_keys_file, inout_predict_reference_keys_file.replace('.npy', '.csv')]
    list_calls_all.append(new_call)


    # Move results file one basedir down
    in_results_file  = join_path_names(output_predict_binary_masks_path, name_output_results_metrics_file)
    out_results_file = join_path_names(output_basedir, name_output_results_metrics_file)

    new_call = ['mv', in_results_file, out_results_file]
    list_calls_all.append(new_call)



    # Iterate over the list and carry out call serially
    for icall in list_calls_all:
        print_call(icall)
        try:
            launch_call(icall)
        except Exception as ex:
            traceback.print_exc(file=sys.stdout)
            message = 'Call failed. Stop pipeline...'
            catch_error_exception(message)
        print('\n')
    # endfor



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_model_file', type=str)
    parser.add_argument('output_basedir', type=str)
    parser.add_argument('--basedir', type=str, default=BASEDIR)
    parser.add_argument('--post_thresholds_values', type=str, nargs='*', default=[POST_THRESHOLD_VALUE])
    parser.add_argument('--list_type_metrics_result', type=str2list_string, default=LIST_TYPE_METRICS_RESULT)
    parser.add_argument('--testing_datadir', type=str, default=NAME_TESTINGDATA_RELPATH)
    parser.add_argument('--is_connected_masks', type=str2bool, default=False)
    args = parser.parse_args()

    print("Print input arguments...")
    for key, value in vars(args).items():
        print("\'%s\' = %s" %(key, value))

    main(args)