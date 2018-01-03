"""Drives the process of translating Hack VM into Hack assembly"""
import sys 
from parser import HackParser, ParserError
from translation_unit import TranslationUnit

# Check for file name
if len(sys.argv) != 2:
    print("Usage: main.py file.vm")
    sys.exit()

# If we got here then we have a file name to work with
IN_FILE = sys.argv[1]

# Check input file's extension
if not IN_FILE.endswith('.vm'):
    print("Input file must end in '.vm'")
    sys.exit()

# Set output file name
OUT_FILE = IN_FILE[0:-3] + '.asm'

print('Staring translation...')

with open(IN_FILE) as filename:
    PARSER = HackParser(filename.readlines(), TranslationUnit(IN_FILE[0:-3]))

try:
    ASM = PARSER.run()
    # print(''.join(ASM))
    with open(OUT_FILE, 'w') as output_file:
        for command in ASM:
            output_file.write(command)
except ParserError as err:
    MSG = f'- Parser error on line number {err.line_no}:\n  '
    print(MSG + str(err))
except ValueError as err:
    MSG = f'- Translator error:\n  '
    print(MSG + str(err))

print('Translation finished')
