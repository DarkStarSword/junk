#!/bin/sh -e

# Use in place of objdump, but converts the virtual offsets on each assembly
# line into a file offset to make it easier to later hexedit the executable.
#
# ./objdump_file_offsets.sh d3d9.dll --start-address=0xfoo --stop-address=0xbar -M intel --no-show-raw-insn
#
# The output is not suited to pipe directly back into an assembler (more a
# statement of syntax differences and "convenience" translations of assemblable
# relative addresses into unassemblable absolute addresses between x86
# disassemblers and assemblers than this script, at least I can't find any
# combination of x86 disassembler that produces output that can be fed back
# into an x86 assembler without considerable fixup work, even when the
# disassembler and assembler comes from the same project... I feel like I must
# be missing some option - what do the crackers use?), but manual use of yasm
# or nasm to assemble individual instructions then hexediting them in is doable
# (GNU assembler is usable for this as well at a pinch, but requires an extra
# step to use the linker to discard the object container it produces).
# e.g. assemble an individual instruction like:
#      echo -e 'bits64\n mov r8,rcx' | yasm - && hexdump -C yasm.out

objdump -F "$@" | gawk 'match($0, /^([0-9a-f]+) <.*> \(File Offset: (0x[0-9a-f]+)\):/, m) {adjust_offset = strtonum("0x" m[1]) - strtonum(m[2]); print $0} match($0, /^\s*([0-9a-f]+)(:.*)$/, m) {printf "0x%x%s\n", (strtonum("0x" m[1]) - adjust_offset), m[2]}'
