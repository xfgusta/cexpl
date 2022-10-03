# cex

Command-line tool to interact with [Compiler Explorer](https://godbolt.org/).

[![asciicast](https://asciinema.org/a/525356.svg)](https://asciinema.org/a/525356)

## Overview

**cex** is able to query all available languages, compilers, build and execute your source code. You can also give some extra arguments, like compiler flags, command-line arguments and STDIN.

The Compiler Explorer API host can be specified with the `-H`/`--host` option.

### List available languages

The `--list-langs` option lists all languages and their IDs:

```text
$ cex --list-langs
ada - Ada
analysis - Analysis
assembly - Assembly
c - C
c++ - C++
carbon - Carbon
circle - C++ (Circle)
circt - CIRCT
clean - Clean
cpp2_cppfront - Cpp2-cppfront
...
```

The language ID can be used with the `-l`/`--lang` option.

### List available compilers

The `--list-compilers` option lists all compilers and their IDs:

```text
$ cex --list-compilers
386_gl114 - 386 gc 1.14
386_gl115 - 386 gc 1.15
386_gl116 - 386 gc 1.16
386_gl117 - 386 gc 1.17
386_gl118 - 386 gc 1.18
386_gl119 - 386 gc 1.19
386_gltip - 386 gc (tip)
6g141 - amd64 gc 1.4.1
aarchg54 - ARM64 gcc 5.4
arduinomega189 - Arduino Mega (1.8.9)
...
```

It is also possible to list the compilers for a specific language. For example, `cex --list-compilers python` will list all available Python compilers.

The compiler ID can be used with the `-c`/`--compiler` option.

### Compilation and execution

In order to compile, you need to pass the file containing the source code. **cex** will try to figure out the language and its default compiler based on the file extension. You can specify the language and/or the compiler with `--lang` and/or `--compiler` option, as said above.

```text
$ cex love.c
.LC0:
        .string "<3"
main:
        push    rbp
        mov     rbp, rsp
        mov     edi, OFFSET FLAT:.LC0
        call    puts
        mov     eax, 0
        pop     rbp
        ret
```

The source code:

```c
#include <stdio.h>

int main() {
    printf("<3\n");
    return 0;
}
```

You can pass options to the compiler with the `--cflags` option.

#### Comparing source code and assembly

Use the `-C`/`--compare` option to compare the source code with the assembly:

```text
$ cex --compare --cflags=-Ofast love.c
.LC0:
        .string "<3"
main:
3 int main() {
        sub     rsp, 8
4 printf("<3\n");
        mov     edi, OFFSET FLAT:.LC0
        call    puts
6 }
        xor     eax, eax
        add     rsp, 8
        ret
```

#### Execution

The `-e`/`--exec` option executes the code:

```text
$ cex --exec --skip-asm love.c
STDOUT:
<3
```

If you don't want to see the generated assembly, use the `-s`/`--skip-asm` option.

##### Arguments and input

You can pass a list of arguments with the `-a`/`--args` option. For example, `cex --args one two three --exec main.c`. The same applies to the `--stdin` option:

```text
$ cex --skip-asm --exec --stdin "Gustavo Costa" 20 -- hi.py
STDOUT:
Gustavo Costa, 20 years old
```

The source code:

```python
name = input()
age = input()
print(f'{name}, {age} years old')
```

#### Saving your results

You can generate a short link for the compilation with the `-L`/`--link` option.
