'''
uses MediaConch to validate media files
'''
import os
import logging
import pathlib
import subprocess
import argparse
import make_log
import util


def run_mediaconch(media_fullpath, policy_fullpath):
    '''
    actually calls MediaConch and handles output

    returncode == 0 means that MC ran on the file
    returncode == 1 means that MC had a problem, like file didn't exist

    output.stdout == True when MC runs successfully
    output.stdout == False when MC has a problem
    output.stderr == True when MC has a problem

    output.stdout.startswith('pass') when file passes
    output.stdout.startswith('fail') when file fails
    '''
    cmd = ["mediaconch", "-p", str(policy_fullpath), str(media_fullpath)]
    output = util.run_command(cmd, return_output=True)
    if output.startswith('pass'):
        logger.info(f"file {media_fullpath.name} passed validation")
        return True
    elif output.startswith('fail'):
        logger.info(f"file {media_fullpath.name} failed validation")
        return output
    else:
        raise RunetimeError("the script encountered an error trying to validate that file")


def get_files_to_validate(folder_path):
    '''
    if we're running this in batch mode
    we need to get every file with .mkv or .dv extension
    '''
    extensions_to_check = [".mkv", ".dv"]
    all_files = []
    for ext in extensions_to_check:
        files_w_this_ext = folder_path.glob('**/*' + ext)
        all_files.extend(files_w_this_ext)
    return all_files


def validate_media(kwvars):
    '''
    manages the process of validating media files with MediaConch
    '''
    policy_fullpath = pathlib.Path(kwvars['policy'])
    fails = []
    if not kwvars['daid']:
        logger.info(f"validating every file in {kwvars['dadir']}")
        files_to_validate = get_files_to_validate(kwvars['dadir'])
        logger.info(f"found {len(files_to_validate)} files to validate")
    else:
        if kwvars['dadir']:
            media_path = pathlib.Path(kwvars['dadir'])
        else:
            media_path = os.getcwd()
            logger.warning(f"no Digital Asset Directory (-dadir) supplied, using current working directory: {media_path}")
            media_path = pathlib.Path(media_path)
        files_to_validate = [media_path / kwvars['daid']]
    for file in files_to_validate:
        logger.info(f"validating {file}...")
        result = run_mediaconch(file, policy_fullpath)
        if result is not True:
            fails.append({str(media_fullpath): result})
    if fails:
        logger.warning(f"{len(fails)} files did not pass validation")
        for failed_file in fails:
            logger.warning(pformat(failed_file))
            input("check that out")


def parse_args(args):
    '''
    returns dictionary of arguments parsed for our use
    '''
    kwvars = {}
    if args.quiet:
        kwvars['loglevel_print'] = logging.WARNING
    elif args.verbose:
        kwvars['loglevel_print'] = logging.DEBUG
    else:
        kwvars['loglevel_print'] = logging.INFO
    if not args.daid:
        raise RuntimeError("no Digital Asset ID (-daid) supplied, exiting...")
    kwvars['daid'] = args.daid
    kwvars['dadir'] = args.dadir
    if not args.policy:
        raise RuntimeError("no MediaConch Policy (-p) supplied, exiting...")
    kwvars['policy'] = args.policy
    return kwvars


def init_args():
    '''
    initializes arguments from the command line
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-q', '--quiet', dest='quiet',
                        action='store_true', default=False,
                        help="run script in quiet mode. "
                        "only print warnings and errors to command line")
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', default=False,
                        help="run script in verbose mode. "
                        "print all log messages to command line")
    parser.add_argument('-daid', '--digital_asset_id', dest='daid', default=None,
                        help="the Digital Asset ID we would like to embed metadata for")
    parser.add_argument('-dadir', '--digital_asset_directory', dest='dadir', default=None,
                        help="the directory where the Digital Asset is located")
    parser.add_argument('-p', '--policy', dest='policy', default=None,
                        help="the MediaConch policy that we want to validate against")
    args = parser.parse_args()
    return args


def main():
    '''
    do the thing
    '''
    print("starting...")
    args = init_args()
    kwvars = parse_args(args)
    global logger
    logger = make_log.init_log(loglevel_print=kwvars['loglevel_print'])
    validate_media(kwvars)
    logger.info("embed_md has completed successfully")


if __name__ == '__main__':
    main()
