#-------------------------------------------------------------------------------
# Name:        Nand2Tetris Assembler
# Purpose:     Translate prog.asm into prog.hack to run on the Hack computer
#
# Author:      szaitseff
#
# Created:     06.03.2018
# Copyright:   (c) szaitseff 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()


class Assembler(object):
    ''' Translates assembly programs into binary code.'''
    def __init__(self, prog_asm, prog_hack):
        self.prog_asm = open(prog_asm)
        self.prog_hack = open(prog_hack, 'w')
        self.A_COMMAND = 0
        self.C_COMMAND = 1
        self.L_COMMAND = 2
        self.counter = 0            # ROM counter
        self.line = -1              # current line counter in the file
        self.command = ""           # commands are strings
        self.address = 16           # RAM address for variables


    def assemble(self, prog_asm, prog_hack):
        ''' Does assembly. '''
        symbols = SymbolTable()             # an instance of SymbolTable class
        code = Code(prog_asm, prog_hack)    # instance of Code class

        ''' First pass: bind labels to ROM addresses. '''
        parser_1 = Parser(prog_asm, prog_hack)  # an instance of Parser class
        while parser_1.hasMoreCommands():
            parser_1.advance()      # removes comments and white spaces
            if parser_1.commandType() == self.L_COMMAND:
                label = parser_1.symbol()
                symbols.addEntry(label, self.counter)   # ROM address
            else:
                self.counter += 1   # for A_COMMAND and C_COMMAND

        ''' Second pass: replace symbols with number & complete translation.'''
        parser_2 = Parser(prog_asm, prog_hack)  # an instance of Parser class
        while parser_2.hasMoreCommands():
            parser_2.advance()
            if parser_2.commandType() == self.A_COMMAND:
                try:
                    addr = int(parser_2.symbol())
                    self.prog_hack.write('{0:0>16b}\n'.format(addr))
                except ValueError:
                    if symbols.contains(parser_2.symbol()):
                        addr = symbols.getAddress(parser_2.symbol())
                        self.prog_hack.write('{0:0>16b}\n'.format(addr))
                    else:
                        symbols.addEntry(parser_2.symbol(), self.address) # RAM
                        self.address += 1
                        addr = symbols.getAddress(parser_2.symbol())
                        self.prog_hack.write('{0:0>16b}\n'.format(addr))

            elif parser_2.commandType() == self.C_COMMAND:
                dest = code.dest(parser_2.dest())
                comp = code.comp(parser_2.comp())
                jump = code.jump(parser_2.jump())
                self.prog_hack.write('111{0}{1}{2}\n'.format(comp, dest, jump))
            else:
                pass

        self.prog_asm.close()
        self.prog_hack.close()

class Parser(Assembler):
    ''' Breaks each assembly command into its underlying components
    (fields and symbols). In addition, removes all white space and comments.
    '''
    def __init__(self, prog_asm, prog_hack):
        Assembler.__init__(self, prog_asm, prog_hack)
        self.lines = self.prog_asm.readlines()  # read & return a list of all lines

    def hasMoreCommands(self):
        ''' Are there more commands in the input? '''
        if (self.line + 1) < len(self.lines):
            return True
        else:
            return False

    def advance(self):
        ''' Reads the next command from the input and makes it the current
        command. Should be called only if hasMoreCommands() is true.
        '''
        self.line += 1
        self.command = self.lines[self.line]
        self.command = self.command.split('//')[0]
        self.command = self.command.split('\n')[0]
        self.command = self.command.strip()
        if self.command == '':
            self.advance()
        else:
            return self.command

    def commandType(self):
        ''' Returns the type of the current command:
        A_COMMAND for @Xxx where Xxx is either a symbol ot a decimal number
        C_COMMAND for dest=comp;jump
        L_COMMAND (pseudocommand) for (Xxx) where Xxx is a symbol. '''

        if self.command[0] == '@':
            return self.A_COMMAND
        elif self.command[0] == '(':
            return self.L_COMMAND
        else:
            return self.C_COMMAND

    def symbol(self):
        ''' Returns the symbol or decimal Xxx of the current command @Xxx or
        (Xxx). Should be called only when commandType() is A_COMMAND or L_COMMAND. '''
        self.command = self.command.split(')')[0]
        return self.command[1:]

    def dest(self):
        ''' Returns the dest mnemonic in the current C-command (8 possibilities).
        Should be called only when commandType() is C_COMMAND. '''
        dest_comp = self.command.split(";")[0]
        if len(dest_comp.split("=")) == 2:
            return dest_comp.split("=")[0]
        else:
            return ""

    def comp(self):
        ''' Returns the comp mnemonic in the current C-command (28 possibilities).
        Should be called only when commandType() is C_COMMAND. '''
        dest_comp = self.command.split(";")[0]
        if len(dest_comp.split("=")) == 2:
            return dest_comp.split("=")[1]
        else:
            return dest_comp

    def jump(self):
        ''' Returns the jump mnemonic in the current C-command (8 possibilities).
            Should be called only when commandType() is C_COMMAND. '''
        try:
            return self.command.split(";")[1]
        except IndexError:
            return ""

class Code(Assembler):
    ''' Translates Hack assembly language mnemonics into binary codes. '''

    def dest(self, mnemonic):
        ''' Returns the binary code of the dest mnemonic (3 bits). '''
        dest_dict = {
              'M':'001',
              'D':'010',
             'MD':'011',
              'A':'100',
             'AM':'101',
             'AD':'110',
            'AMD':'111'}
        return dest_dict.get(mnemonic, '000')

    def comp(self, mnemonic):
        ''' Returns the binary code of the comp mnemonic (7 bits). '''
        comp_dict = {
              '0': '0101010',
              '1': '0111111',
             '-1': '0111010',
              'D': '0001100',
              'A': '0110000',   'M': '1110000',
             '!D': '0001101',
             '!A': '0110001',  '!M': '1110001',
             '-D': '0001111',
             '-A': '0110011',  '-M': '1110011',
            'D+1': '0011111',
            'A+1': '0110111', 'M+1': '1110111',
            'D-1': '0001110',
            'A-1': '0110010', 'M-1': '1110010',
            'D+A': '0000010', 'D+M': '1000010',
            'D-A': '0010011', 'D-M': '1010011',
            'A-D': '0000111', 'M-D': '1000111',
            'D&A': '0000000', 'D&M': '1000000',
            'D|A': '0010101', 'D|M': '1010101'}
        return comp_dict.get(mnemonic, '0000000')

    def jump(self, mnemonic):
        ''' Returns the binary code of the jump mnemonic (3 bits). '''
        jump_dict = {
            'JGT': '001',
            'JEQ': '010',
            'JGE': '011',
            'JLT': '100',
            'JNE': '101',
            'JLE': '110',
            'JMP': '111'}
        return jump_dict.get(mnemonic, '000')

class SymbolTable(Assembler):
    ''' Keeps mapping between symbolic labels and numeric addresses. '''
    def __init__(self):
        Assembler.__init__(self, prog_asm, prog_hack)

        self.dict = {
             'SP': 0,
            'LCL': 1,
            'ARG': 2,
           'THIS': 3,
           'THAT': 4,
             'R0': 0,
             'R1': 1,
             'R2': 2,
             'R3': 3,
             'R4': 4,
             'R5': 5,
             'R6': 6,
             'R7': 7,
             'R8': 8,
             'R9': 9,
            'R10': 10,
            'R11': 11,
            'R12': 12,
            'R13': 13,
            'R14': 14,
            'R15': 15,
         'SCREEN': 16384,
            'KBD': 24576}


    def addEntry(self, symbol, address):
        ''' Adds the pair (symbol, address) to the table. '''
        self.dict[symbol] = address
        return self.dict

    def contains(self, symbol):
        ''' Does the symbol table contain the given symbol? '''
        return (symbol in self.dict)

    def getAddress(self, symbol):
        ''' Returns the address associated with the symbol. '''
        return self.dict[symbol]



prog_asm = 'Pong.asm'
prog_hack = 'Pong.hack'
assembler = Assembler(prog_asm, prog_hack)

assembler.assemble(prog_asm, prog_hack)

t = open(prog_hack)
print(t.readlines())
t.close()









