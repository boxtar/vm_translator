import unittest
import parser as Parser
from parser import COMMAND_TYPES
from translation_unit import TranslationUnit

class TestVMTranslator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.translator = TranslationUnit('UnitTest')

        
    def test_translation_unit_push(self):
        """ Tests the translation of the push command """
        command = 'push constant 100'
        expecting = (
            '@100\n'
            'D=A\n'
            '// --- Push D Reg to stack ---\n'
            '@SP\n'
            'A=M\n'
            'M=D\n'
            '@SP\n'
            'M=M+1\n'
        )
        self.assertEqual(
            self.translator.push_command(
                Parser.get_arg1(command)[0],
                Parser.get_arg2(command)[0]
            ),
            expecting
        )
        

    # ARITHMETIC COMMAND TESTS
    def test_is_arithmetic_command(self):
        test_commands = ['add', 'sub', 'gt', 'lt']

        for command in test_commands:
            self.assertEqual(
                Parser.get_command_type(command)[0], COMMAND_TYPES['C_ARITHMETIC'])


    # POP COMMAND TESTS
    def test_is_pop_command(self):
        # Good pop command
        self.assertEqual(
            Parser.get_command_type('pop local 0')[0], COMMAND_TYPES['C_POP'])

        # Bad pop command
        self.assertEqual(
            Parser.get_command_type('pop constant 3')[1], False)


    # PUSH COMMAND TESTS
    def test_is_push_command(self):
        # Good push command
        self.assertEqual(
            Parser.get_command_type('push local 2')[0], COMMAND_TYPES['C_PUSH'])

        # Bad push command
        self.assertEqual(
            Parser.get_command_type('push unknown 0')[1], False)


    # COMMAND_TYPE ERROR TESTS
    def test_is_error_command(self):
        # 1 Part
        self.assertEqual(
            Parser.get_command_type('ada')[1], False)

        # 2 Parts
        self.assertEqual(
            Parser.get_command_type('poppy pushy')[1], False)

        # 3 Parts
        self.assertEqual(
            Parser.get_command_type('pushy local 9')[1], False)

        # 4 Parts
        self.assertEqual(
            Parser.get_command_type('poppy pushy index 9')[1], False)
    

    # GET_ARG1 TESTS
    def test_get_arg1(self):
        # Success tests
        self.assertEqual(
            Parser.get_arg1('add')[0], 'add')

        self.assertEqual(
            Parser.get_arg1('push local 9')[0], 'local')

        self.assertEqual(
            Parser.get_arg1('pop argument 0')[0], 'argument')
            

        # Error tests
        self.assertEqual(
            Parser.get_arg1('ada')[1], False)

        self.assertEqual(
            Parser.get_arg1('push lexer 8')[1], False)

        self.assertEqual(
            Parser.get_arg1('pop constant 12')[1], False)

        self.assertEqual(
            Parser.get_arg1('pop to unknown 12')[1], False)


    # GET_ARG2 TESTS
    def test_get_arg2(self):
        # Success Tests
        self.assertEqual(Parser.get_arg2('push constant 23')[0], '23')
        self.assertEqual(Parser.get_arg2('pop local 3')[0], '3')

        # Error Tests
        self.assertEqual(Parser.get_arg2('push unknown 3')[1], False)
        self.assertEqual(Parser.get_arg2('pop constant 23')[1], False)


if __name__ == '__main__':
    unittest.main()
