// --- gt ---
@SP
AM=M-1
D=M
A=A-1
D=M-D
@GT1
D;JGT
D=-1
@GT1_END
0;JMP
(GT1)
D=0
(GT1_END)
@SP
A=M-1
M=D
// --- or ---
@SP
AM=M-1
D=M
A=A-1
M=D|M
// --- and ---
@SP
AM=M-1
D=M
A=A-1
M=D&M
