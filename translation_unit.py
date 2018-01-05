"""This module contains the TranslationUnit class"""

class TranslationUnit:
    """This class takes VM Bytecode commands and translates them to Hack ASM commands.

    The public api is:
        push_command(segment, offset),
        pop_command(segment, offset),
        arithmetic_command(command),
        label_command(label),
        unconditional_goto_command(label),
        conditional_goto_command(label)

    Args:
        static_prefix (str): Name of file. Used to label static variables.

    Attributes:
        static_prefix (str): Name of file. Used to label static variables.
        static_labels (dict): Dictionary of static labels (key) and their associated register no (value).
        eq_label_count (int): Count of eq command occurences for unique labels.
        gt_label_count (int): Count of gt command occurences for unique labels.
        lt_label_count (int): Count of lt command occurences for unique labels.

    """

    __MEMORY_SEGMENTS = ('local', 'argument', 'this', 'that',
                         'constant', 'pointer', 'static', 'temp')

    __MEM_SEG_MAP = {'local': 'LCL', 'argument': 'ARG',
                     'this': 'THIS', 'that': 'THAT'}

    __ARITHMETIC_COMMANDS = ('add', 'sub', 'neg', 'eq',
                             'gt', 'lt', 'and', 'or', 'not')

    __VAR_BASE_ADDRESS = 16 # 0x0010

    __TEMP_BASE_ADDRESS = 5 # 0x0005

    __TEMP_MAX_ADDRESS = 12 # 0x000C

    __THIS_POINTER = 0
    
    __THAT_POINTER = 1

    __TRUE = -1
    __FALSE = 0

    # --- Constructor --- #
    def __init__(self, static_prefix):
        """Static Prefix is required for creating static variable labels"""
        self.static_prefix = static_prefix
        self.static_labels = {}
        self.eq_label_count = 0
        self.gt_label_count = 0
        self.lt_label_count = 0


    # --- Push Methods --- #
    def push_command(self, segment, offset):
        """This function translates a push command to hack asm.

        Args:
            segment (str): The memory segment that the value is being pushed from.
            offset (number): The offset within segement to be pushed to stack.
        """
        if segment in self.__MEMORY_SEGMENTS:
            if segment == 'constant':
                return self.__push_constant(offset) + self.__push_d_reg_to_stack()
            elif segment == 'static':
                return self.__push_static(offset) + self.__push_d_reg_to_stack()
            elif segment == 'temp':
                return self.__push_temp(offset) + self.__push_d_reg_to_stack()
            elif segment == 'pointer':
                return self.__push_pointer(offset) + self.__push_d_reg_to_stack()
            # local, argument, this, that
            return self.__push_normal_segment(segment, offset) + self.__push_d_reg_to_stack()
        else:
            raise ValueError(segment + ' is not a valid memory segment')

    def __push_static(self, offset):
        label = self.__get_static_label(offset)
        return (f'@{label}\n'
                'D=M\n')

    @classmethod
    def __push_normal_segment(cls, segment, offset):
        """This function returns hack asm for a push to local, argument, this or that."""
        return (f'@{cls.__MEM_SEG_MAP[segment]}\n'
                'D=M\n'
                f'@{offset}\n'
                'A=D+A\n'
                'D=M\n')

    @classmethod
    def __push_pointer(cls, pointer):
        # Raises exception if pointer value out with limits
        cls.__check_pointer_value(pointer)
        if pointer == cls.__THIS_POINTER:
            return (f'@{cls.__MEM_SEG_MAP["this"]}\n'
                    'D=M\n')
        else:
            return (f'@{cls.__MEM_SEG_MAP["that"]}\n'
                    'D=M\n')
    
    @classmethod
    def __push_temp(cls, offset):
        cls.__check_temp_address(offset)
        return (f'@{cls.__TEMP_BASE_ADDRESS + offset}\n'
                'D=M\n')

    @staticmethod
    def __push_constant(value):
        return (f'@{value}\n'
                'D=A\n')

    @staticmethod
    def __push_d_reg_to_stack():
        return ('@SP\n'
                'A=M\n'
                'M=D\n'
                '@SP\n'
                'M=M+1\n')


    # --- Pop Methods --- #
    def pop_command(self, segment, offset):
        """This function translates a pop command to hack asm.

        Args:
            segment (str): The memory segment to pop to (local, static etc...).
            offset (number): the offset within segment to pop to.
        """

        if segment in self.__MEMORY_SEGMENTS:
            if segment == 'constant':
                # If trying to pop to constant - raise Exception
                raise ValueError('Cannot pop to constant')
            elif segment == 'temp':
                # The below will raise an exception if offset is beyond temp seg
                self.__check_temp_address(offset)
                code = self.__pop_stack_to_d_reg()
                code += (f'@{self.__TEMP_BASE_ADDRESS + offset}\n'
                         'M=D\n')
                return code
            elif segment == 'static':
                label = self.__get_static_label(offset)
                code = self.__pop_stack_to_d_reg()
                code += (
                    f'@{label}\n'
                    'M=D\n')
                return code
            elif segment == 'pointer':
                # Raises exception if pointer value out with limits
                self.__check_pointer_value(offset)
                if offset == self.__THIS_POINTER:
                    label = self.__MEM_SEG_MAP['this']
                else:
                    label = self.__MEM_SEG_MAP['that']
                code = self.__pop_stack_to_d_reg()
                code += (
                    f'@{label}\n'
                    'M=D\n')
                return code
            else:
                if offset > 1:
                    # If offset > 1 then we have a bit of work to do
                    # in order to setup target memory address
                    code = (
                        f'@{self.__MEM_SEG_MAP[segment]}\n' # Address target base pointer
                        'D=M\n' # Bring base address of target memory segment into D register
                        f'@{offset}\n' # Set A register to offset so that it can be added to base address
                        'D=D+A\n' # Add offset to base address
                        '@R13\n' # Address virtual register 13 
                        'M=D\n' # Store targeted memory address into R13
                    )
                    code += self.__pop_stack_to_d_reg()
                    code += (
                        '@R13\n'
                        'A=M\n'
                        'M=D\n'
                    )
                    return code
                elif offset == 1:
                    # If offset == 1 then we can cut down the number
                    # of assembly lines produced.
                    code = self.__pop_stack_to_d_reg()
                    code += (
                        f'@{self.__MEM_SEG_MAP[segment]}\n'
                        'A=M+1\n'
                        'M=D\n'
                    )
                    return code
                else:
                    # offset is 0 - can do in 7 lines of asm
                    code = self.__pop_stack_to_d_reg()
                    code += (
                        f'@{self.__MEM_SEG_MAP[segment]}\n'
                        'A=M\n'
                        'M=D\n'
                    )
                    return code
        else:
            raise ValueError(segment + ' is not a valid memory segment')

    @staticmethod
    def __pop_stack_to_d_reg():
        return (
            '@SP\n'
            'AM=M-1\n'  # Decrement and Dereference Stack pointer
            'D=M\n'  # Bring target value into D register
        )


    # --- Arithmetic & Logical methods --- #
    def arithmetic_command(self, command):
        """This function translates an arithmetic command to hack asm.

        Args:
            command (str): The arithmetic command to be translated to ASM.
        """
        if command in self.__ARITHMETIC_COMMANDS:
            if command == 'add':
                return self.__add_command()
            elif command == 'sub':
                return self.__sub_command()
            elif command == 'neg':
                return self.__neg_command()
            elif command == 'eq':
                return self.__eq_command()
            elif command == 'gt':
                return self.__gt_command()
            elif command == 'lt':
                return self.__lt_command()
            elif command == 'and':
                return self.__and_command()
            elif command == 'or':
                return self.__or_command()
            elif command == 'not':
                return self.__not_command()

    @staticmethod
    def __add_command():
        return TranslationUnit.__add_or_sub_command('add')

    @staticmethod
    def __sub_command():
        return TranslationUnit.__add_or_sub_command('sub')

    @staticmethod
    def __neg_command():
        return ('@SP\n'
                'A=M-1\n'
                'M=-M\n')

    @staticmethod
    def __and_command():
        return TranslationUnit.__logical_command('&')

    @staticmethod
    def __or_command():
        return TranslationUnit.__logical_command('|')

    @staticmethod
    def __not_command():
        return ('@SP\n'
                'A=M-1\n'
                'M=!M\n')

    def __eq_command(self):
        self.eq_label_count += 1
        return self.__comparison_command(f'EQ{self.eq_label_count}', 'JEQ')

    def __gt_command(self):
        self.gt_label_count += 1
        return self.__comparison_command(f'GT{self.gt_label_count}', 'JGT')

    def __lt_command(self):
        self.lt_label_count += 1
        return self.__comparison_command(f'LT{self.lt_label_count}', 'JLT')
        
    @staticmethod
    def __add_or_sub_command(command):
        command = 'M=M+D\n' if command == 'add' else 'M=M-D\n'
        code = TranslationUnit.__pop_stack_to_d_reg()
        code += f'A=A-1\n{command}'
        return code

    @staticmethod
    def __comparison_command(label, condition):
        """Produces Hack asm for a gt, lt or eq command.

        Args:
            label (str): Label to use for conditional jumps
            condition (str): Condition to use for jump
        """
        code = TranslationUnit.__pop_stack_to_d_reg()
        code += (
            'A=A-1\n'
            'D=M-D\n'
            f'@{label}\n'
            f'D;{condition}\n'
            f'D={TranslationUnit.__FALSE}\n'
            f'@{label}_END\n'
            '0;JMP\n'
            f'({label})\n'
            f'D={TranslationUnit.__TRUE}\n'
            f'({label}_END)\n'
            '@SP\n'
            'A=M-1\n'
            'M=D\n'
        )
        return code

    @staticmethod
    def __logical_command(logical_op):
        code = TranslationUnit.__pop_stack_to_d_reg()
        code += (
            'A=A-1\n'
            f'M=D{logical_op}M\n'
        )
        return code


    # --- Branching methods --- #
    @staticmethod
    def label_command(label):
        """Returns Hack asm for declaring a label"""
        return f'({label})\n'

    @staticmethod
    def unconditional_goto_command(label):
        """Returns Hack asm for unconditionally branching to a given label"""
        return (
            f'@{label}\n'
            '0;JMP\n'
        )

    @staticmethod
    def conditional_goto_command(label):
        """Returns Hack asm for conditionally branching to a given label"""
        code = TranslationUnit.__pop_stack_to_d_reg()
        code += (
            'D=D+1\n' # TRUE = -1 so adding 1 to it should make it zero; else it's not TRUE
            f'@{label}\n'
            'D;JEQ\n' # Jump if D = 0 (-1 + 1)
        )
        return code


    # --- Other methods --- #
    def __get_static_label(self, offset):
        label = f'{self.static_prefix}.{str(offset)}'
        if not label in self.static_labels:
            count = len(self.static_labels)
            self.static_labels[label] = self.__VAR_BASE_ADDRESS + count
        return self.static_labels[label]
    
    @staticmethod
    def __store_d_reg_in_vm_temp(temp):
        if temp >= 13 and temp <= 15:
            return f'@R{temp}\nM=D\n'
        else:
            raise ValueError('VM can only store temps in RAM[13] to RAM[15]')
    
    @classmethod
    def __check_temp_address(cls, offset):
        base_addr = cls.__TEMP_BASE_ADDRESS
        max_addr = cls.__TEMP_MAX_ADDRESS

        if offset < 0 or (base_addr + offset) > max_addr:
            raise ValueError(
                f'{offset} is out of temp segment bounds (8 virtual registers - 0 to 7)')

    @classmethod
    def __check_pointer_value(cls, value):
        if value != cls.__THIS_POINTER and value != cls.__THAT_POINTER:
            raise ValueError(
                'value provided to push pointer can only be 0 or 1\n\t' + str(value) + ' provided')
