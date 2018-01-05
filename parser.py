"""This module contains the HackParser and ParserError classes"""

class HackParser:
    """This class parses and controls translation of the provided source file.

    This class will parse the source file one line at a time, passing each line
    to the appropriate method in the provided translator instance for translation
    to Hack asm.

    Args:
        source_commands (List/Tuple of Strings): List of source comands to parse.
        translator: Implementation of Hack Source Translator to use.

    Attributes:
        current_command (str): Current command being parsed.
        line_no (int): Current line number of source being parsed.
        source_commands (List/Tuple of Strings): List of source comands to parse.
        translator: Implementation of Hack Source Translator to use.
    """

    # Command type names mapped to values
    __COMMAND_TYPES = {
        'C_ARITHMETIC': 1, 'C_PUSH': 2, 'C_POP': 3, 'C_LABEL': 4, 'C_GOTO': 5,
        'C_IF': 6, 'C_FUNCTION': 7, 'C_RETURN': 8, 'C_CALL': 9
    }

    # Memory segments that can be popped to
    __POP_STACKS = ['static', 'local', 'this', 'that',
                    'argument', 'pointer', 'temp']

    # Memory segments that can be pushed to (all same as pop plus constant seg)
    __PUSH_STACKS = __POP_STACKS[:]
    __PUSH_STACKS.append('constant')

    # Arithmetic commands
    __ARITHMETIC_COMMANDS = ('add', 'sub', 'neg',
                             'eq', 'gt', 'lt', 'and', 'or', 'not')

    # Command types that have a 2nd argument
    __ARG2_LIST = [
        __COMMAND_TYPES['C_PUSH'],
        __COMMAND_TYPES['C_POP'],
        __COMMAND_TYPES['C_FUNCTION'],
        __COMMAND_TYPES['C_CALL']
    ]

    def __init__(self, source_commands, translator):
        self.source_commands = []
        for command in source_commands:
            self.source_commands.append(command.strip())
        self.translator = translator
        self.line_no = 0
        self.current_command = ''

    def run(self):
        """Drives the translation process"""
        if not self.source_commands:
            raise ParserError("No source commands provided", False, 0)
        # This list will be filled with assembly from translator
        asm_list = []
        for command in self.source_commands:
            self.line_no += 1
            # If current command is not a comment or blank line then process command
            if not self.__is_comment_or_empty_line(command):
                command_type = self.__get_command_type(command)
                if command_type == self.__COMMAND_TYPES['C_PUSH']:
                    segment = self.__get_arg_1(command, command_type, self.line_no)
                    offset = self.__get_arg_2(command, command_type, self.line_no)
                    asm = self.translator.push_command(segment, offset)
                    asm_list.append(f'// --- {command} ---\n{asm}')
                elif command_type == self.__COMMAND_TYPES['C_POP']:
                    segment = self.__get_arg_1(command, command_type, self.line_no)
                    offset = self.__get_arg_2(command, command_type, self.line_no)
                    asm = self.translator.pop_command(segment, offset)
                    asm_list.append(f'// --- {command} ---\n{asm}')
                elif command_type == self.__COMMAND_TYPES['C_ARITHMETIC']:
                    asm = self.translator.arithmetic_command(command)
                    asm_list.append(f'// --- {command} ---\n{asm}')
                elif command_type == self.__COMMAND_TYPES['C_LABEL']:
                    label = self.__get_arg_1(command, command_type, self.line_no)
                    asm = self.translator.label_command(label)
                    asm_list.append(f'// --- {command} ---\n{asm}')
                elif command_type == self.__COMMAND_TYPES['C_GOTO']:
                    label = self.__get_arg_1(command, command_type, self.line_no)
                    asm = self.translator.unconditional_goto_command(label)
                    asm_list.append(f'// --- {command} ---\n{asm}')
                elif command_type == self.__COMMAND_TYPES['C_IF']:
                    label = self.__get_arg_1(command, command_type, self.line_no)
                    asm = self.translator.conditional_goto_command(label)
                    asm_list.append(f'// --- {command} ---\n{asm}')
        return asm_list
                    
    def __get_command_type(self, command):
        """Returns the type of the command passed in (or raises an Exception)"""
        # Split command into parts (space is default delimiter)
        command = command.split()
        if len(command) == 3:
            # If command has 3x parts then it could be a push to or pop from stack
            if command[0] == 'push':
                return self.__check_push_command(command, self.line_no)
            elif command[0] == 'pop':
                return self.__check_pop_command(command, self.line_no)
        elif len(command) == 2:
            if command[0] == 'label':
                return self.__COMMAND_TYPES['C_LABEL']
            elif command[0] == 'goto':
                return self.__COMMAND_TYPES['C_GOTO']
            elif command[0] == 'if-goto':
                return self.__COMMAND_TYPES['C_IF']
        elif len(command) == 1:
            # If command has 1x part then could be Arithmetic command
            if command[0] in self.__ARITHMETIC_COMMANDS:
                return self.__COMMAND_TYPES['C_ARITHMETIC']
        raise ParserError(
            self.__get_unrecognised_command_msg(' '.join(command)),
            command, self.line_no
        )

    @classmethod
    def __check_push_command(cls, command, line_no):
        """Checks semantics of C_PUSH command"""
        # Provided segment not in available push segments? Raise Exception
        if not command[1] in cls.__PUSH_STACKS:
            raise ParserError(
                cls.__get_unrecognised_mem_seg_msg(command[1]), ' '.join(command), line_no)
        # Provided offset not a digit? Raise Exception
        if not command[2].isdigit():
            raise ParserError(
                cls.__get_illegal_offset_message(command[2]), ' '.join(command), line_no)
        # All good, return push command type
        return cls.__COMMAND_TYPES['C_PUSH']

    @classmethod
    def __check_pop_command(cls, command, line_no):
        """Checks semantics of C_POP command"""
        # Provided segment not in available pop segments? Raise Exception
        if not command[1] in cls.__POP_STACKS:
            raise ParserError(
                cls.__get_unrecognised_mem_seg_msg(command[1]), ' '.join(command), line_no)
        # Provided offset not a digit? Raise Exception
        if not command[2].isdigit():
            raise ParserError(
                cls.__get_illegal_offset_message(command[2]), ' '.join(command), line_no)
        # All good, return pop command type
        return cls.__COMMAND_TYPES['C_POP']
    
    @classmethod
    def __get_arg_1(cls, command, command_type, line_no):
        """Returns the first argument of the given command

        In the case of C_ARITHMETIC, returns the command itself (add, sub etc)
        Should not be called if command is C_RETURN
        """

        if command_type == cls.__COMMAND_TYPES['C_RETURN']:
            raise ParserError("Cannot get arg 1 of return command type", command, line_no)

        command_split = command.split()

        if command_type == cls.__COMMAND_TYPES['C_ARITHMETIC']:
            return command_split[0]
        else:
            return command_split[1]
        raise ParserError(
            "Cannot get argument 1 of command: " + command, command, line_no)

    @classmethod
    def __get_arg_2(cls, command, command_type, line_no):
        """Returns the second argument of the given command
        
        Should only be called for the following command types:
        C_PUSH, C_POP, C_FUNCTION, C_CALL
        """
        command = command.split()
        if command_type in cls.__ARG2_LIST:
            return int(command[2])
        raise ParserError(
            "Cannot get argument 2 of command: " + ' '.join(command), ' '.join(command), line_no)

    @staticmethod
    def __is_comment_or_empty_line(command):
        """Returns True if command is a comment, False otherwise.
        
        This will split command into 2 from the start of the first comment.
        If command begins with a comment then the command is an empty string.
        This also strips out inline comments.

        """
        command = command.strip().split('//', 1)[0]
        return True if not command else False

    @staticmethod
    def __get_unrecognised_command_msg(command):
        return f'Unrecognised command \'{command}\'\n'

    @staticmethod
    def __get_unrecognised_mem_seg_msg(segment):
        return f'Unrecognised memory segment \'{segment}\'\n'

    @staticmethod
    def __get_illegal_offset_message(offset):
        return f'Illegal offset \'{offset}\'\n'


class ParserError(Exception):
    """Exception class defining an error during parsing a file.

    Args:
        err_message (str): Message describing error
        command (str): Command that caused error
        line_no (int): Line number in source file where error occured

    Attributes:
        err_message (str): Message describing error
        command (str): Command that caused error
        line_no (int): Line number in source file where error occured
    """

    def __init__(self, err_message, command, line_no):
        super().__init__(err_message)
        self.command, self.line_no = command, line_no
