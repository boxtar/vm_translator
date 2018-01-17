"""Drives the process of translating Hack VM into Hack assembly"""
import sys
import argparse
from pathlib import Path
import os.path
from parser import HackParser, ParserError
from translation_unit import TranslationUnit

def parse_command_line_args(default_outfile_name):
    """Parse Command Line Arguments.
    
    Returns a dictionary with key as argument name.
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--src', dest='source', default='./',
                            help="Source file or directory containing source files to translate")
    arg_parser.add_argument('-o', '--out', dest='output_file', default=default_outfile_name,
                            help=f"Output file name. Default is {default_outfile_name}")
    arg_parser.add_argument('-b', '--boot', dest='bootstrap_required', action='store_true',
                            help='If flag is set then asm output will begin with bootstrap instructions')
    # Parse command line args
    args = arg_parser.parse_args()

    return {
        'source': args.source,
        'output_file': args.output_file,
        'bootstrap_required': args.bootstrap_required
    }

# List of dictionaries containing data on files to be translated.
# Each file dict has a 'filename' and 'commands' key:
# filename is the name of the file including extension.
# commands is a list of lines in the file.
VM_FILES = []

# Create parser instance which requires a translator instance
PARSER = HackParser(TranslationUnit())

# This list will hold all ASM commands from all files being translated.
ASM = []

# Parse command line arguments
ARGS = parse_command_line_args('out.asm')

# If -b, --boot flag provided then set bootstrap code
if ARGS['bootstrap_required']:
    ASM.append(PARSER.translator.get_bootstrap_instructions())

# Source file or directory
SOURCE = ARGS['source']
OUTPUT_FILE = ARGS['output_file']

# Turn -s, --src arg into a Path object
SOURCE = Path(SOURCE)

# Check if source is file, directory or doesn't exist
if SOURCE.is_file():
    with open(SOURCE) as FILE:
        VM_FILES.append({
            'filename': os.path.basename(SOURCE)[0:-3],
            'commands': FILE.readlines()
        })
elif SOURCE.is_dir():
    for VM_FILE in list(SOURCE.glob('./*.vm')):
        with open(VM_FILE) as FILE:
            VM_FILES.append({
                'filename': os.path.basename(VM_FILE)[0:-3],
                'commands': FILE.readlines()
            })
else:
    raise FileNotFoundError(f'{SOURCE} is not a file or directory')

# Start translation process
print('>>> Translation started')

try:
    for VM_FILE in VM_FILES:
        PARSER.set_new_file(VM_FILE)
        ASM += PARSER.run()
except ParserError as err:
    # Parser error
    MSG = f'- Parser error on line number {err.line_no} in {err.filename}.vm:\n  '
    print(MSG + str(err))
    sys.exit()
except ValueError as err:
    # TODO: make this a Translator specific error
    MSG = f'- Translator error:\n  '
    print(MSG + str(err))
    sys.exit()

with open(OUTPUT_FILE, 'w') as output_file:
    for command in ASM:
        output_file.write(command)

print('>>> Translation finished')
# Translation process finished
