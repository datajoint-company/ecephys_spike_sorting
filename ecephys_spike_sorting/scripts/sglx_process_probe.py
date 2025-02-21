import os
import sys
import subprocess
import json

sys.path.append(os.path.dirname(__file__))
from helpers import SpikeGLX_utils
from helpers import log_from_json
from helpers import run_one_probe
from create_input_json import createInputJson


modules = ['kilosort_helper',
           'kilosort_postprocessing',
           'noise_templates',
           'mean_waveforms',
           'quality_metrics']


def run_probe(prb, json_directory, npx_directory,
              session_str, gate_str, trigger_str,
              run_CatGT, catGT_dest, catGT_car_mode,
              catGT_loccar_min_um, catGT_loccar_max_um,
              catGT_cmd_string,
              ks_Th, refPerMS,
              KS2ver=None,
              ks_remDup=0,
              ks_saveRez=1,
              ks_copy_fproc=0,
              ks_templateRadius_um=163,
              ks_whiteningRadius_um=163,
              ks_minfr_goodchannels=0.1,
              c_Waves_snr_um=160,
              ni_present=True,
              ni_extract_string=None):

    # build path to the first probe folder; look into that folder
    # to determine the range of trials if the user specified t limits as
    # start and end
    run_folder_name = session_str + '_g' + gate_str
    prb0_fld_name = run_folder_name + '_imec' + prb
    prb0_fld = os.path.join(npx_directory, run_folder_name, prb0_fld_name)
    first_trig, last_trig = SpikeGLX_utils.ParseTrigStr(
        trigger_str, prb, gate_str, prb0_fld)
    trigger_str = repr(first_trig) + ',' + repr(last_trig)

    # create CatGT command for this probe
    print('Creating json file for CatGT on probe: ' + prb)
    # Run CatGT
    catGT_input_json = os.path.join(json_directory, session_str + prb + '_CatGT' + '-input.json')
    catGT_output_json = os.path.join(json_directory, session_str + prb + '_CatGT' + '-output.json')

    # build extract string for SYNC channel for this probe
    sync_extract = '-SY=' + prb + ',-1,6,500'
    # if this is the first probe processed, process the ni stream with it
    if ni_present:
        catGT_stream_string = '-ap -ni'
        ni_extract_string = ni_extract_string or '-XA=0,1,3,500 -iXA=1,3,3,0  -XD=-1,1,50 -XD=-1,2,1.7 -XD=-1,3,5 -iXD=-1,3,5'
        extract_string = sync_extract + ' ' + ni_extract_string
    else:
        catGT_stream_string = '-ap'
        extract_string = sync_extract
    # build name of first trial to be concatenated/processed;
    # allows reading of the metadata
    run_str = session_str + '_g' + gate_str
    run_folder = run_str
    prb_folder = run_str + '_imec' + prb
    input_data_directory = os.path.join(npx_directory, run_folder, prb_folder)
    fileName = run_str + '_t' + repr(first_trig) + '.imec' + prb + '.ap.bin'
    continuous_file = os.path.join(input_data_directory, fileName)
    metaName = run_str + '_t' + repr(first_trig) + '.imec' + prb + '.ap.meta'
    input_meta_fullpath = os.path.join(input_data_directory, metaName)
    print(input_meta_fullpath)
    createInputJson(catGT_input_json,
                    KS2ver=KS2ver,
                    npx_directory=npx_directory,
                    continuous_file=continuous_file,
                    kilosort_output_directory=catGT_dest,
                    spikeGLX_data=True,
                    input_meta_path=input_meta_fullpath,
                    catGT_run_name=session_str,
                    gate_string=gate_str,
                    trigger_string=trigger_str,
                    probe_string=prb,
                    catGT_stream_string=catGT_stream_string,
                    catGT_car_mode=catGT_car_mode,
                    catGT_loccar_min_um=catGT_loccar_min_um,
                    catGT_loccar_max_um=catGT_loccar_max_um,
                    catGT_cmd_string=catGT_cmd_string + ' ' + extract_string,
                    extracted_data_directory=catGT_dest
                    )
    # create json files for the other modules
    session_id = session_str + '_imec' + prb
    module_input_json = os.path.join(json_directory, session_id + '-input.json')
    # location of the binary created by CatGT, using -out_prb_fld
    run_str = session_str + '_g' + gate_str
    run_folder = 'catgt_' + run_str
    prb_folder = run_str + '_imec' + prb
    data_directory = os.path.join(catGT_dest, run_folder, prb_folder)
    fileName = run_str + '_tcat.imec' + prb + '.ap.bin'
    continuous_file = os.path.join(data_directory, fileName)
    outputName = 'imec' + prb + '_ks2'
    # kilosort_postprocessing and noise_templates modules alter the files
    # that are input to phy. If using these modules, keep a copy of the
    # original phy output
    ks_make_copy = 'kilosort_postprocessing' in modules or 'noise_templates' in modules
    kilosort_output_dir = os.path.join(data_directory, outputName)
    print(data_directory)
    print(continuous_file)
    print('ks_Th: ' + repr(ks_Th) + ' ,refPerMS: ' + repr(refPerMS))
    createInputJson(module_input_json,
                    KS2ver=KS2ver,
                    npx_directory=npx_directory,
                    continuous_file=continuous_file,
                    spikeGLX_data=True,
                    input_meta_path=input_meta_fullpath,
                    kilosort_output_directory=kilosort_output_dir,
                    ks_make_copy=ks_make_copy,
                    noise_template_use_rf=False,
                    catGT_run_name=session_id,
                    gate_string=gate_str,
                    probe_string=str(prb),
                    ks_remDup=ks_remDup,
                    ks_finalSplits=1,
                    ks_labelGood=1,
                    ks_saveRez=ks_saveRez,
                    ks_copy_fproc=ks_copy_fproc,
                    ks_minfr_goodchannels=ks_minfr_goodchannels,
                    ks_whiteningRadius_um=ks_whiteningRadius_um,
                    ks_Th=ks_Th,
                    ks_CSBseed=1,
                    ks_LTseed=1,
                    ks_templateRadius_um=ks_templateRadius_um,
                    extracted_data_directory=catGT_dest,
                    c_Waves_snr_um=c_Waves_snr_um,
                    qm_isi_thresh=refPerMS / 1000
                    )

    # check for existence of log file, create if not there
    logFullPath = os.path.join(catGT_dest, 'ecephys_run_log.csv')
    if not os.path.isfile(logFullPath):
        # create the log file, write header
        log_from_json.writeHeader(logFullPath)

    # actually running the modules for this probe
    run_one_probe.runOne(session_id,
                         json_directory,
                         data_directory,
                         run_CatGT,
                         catGT_input_json,
                         catGT_output_json,
                         modules,
                         module_input_json,
                         logFullPath)


def main():
    json_fp = sys.argv[1]

    with open(json_fp) as f:
        kwargs = json.load(f)

    run_probe(**kwargs)


if __name__ == '__main__':
    main()
