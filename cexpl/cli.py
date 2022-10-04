"""Command-line interface"""

import argparse
import operator
import os.path
import sys
from colorama import Fore, init
import cexpl

api = cexpl.Cexpl()

def main(argv):
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='cexpl',
        description='Command-line tool to interact with Compiler Explorer',
        allow_abbrev=False
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {cexpl.__version__}'
    )

    parser.add_argument(
        '-H', '--host',
        metavar='URL',
        default='https://godbolt.org',
        help='Specify the Compiler Explorer host (default: %(default)s)'
    )

    parser.add_argument(
        '--list-langs',
        action='store_true',
        help='List available languages'
    )

    parser.add_argument(
        '--list-compilers',
        metavar='LANG',
        nargs='?',
        default=False,
        help='List available compilers'
    )

    parser.add_argument(
        '-c', '--compiler',
        help='Specify the compiler'
    )

    parser.add_argument(
        '-l', '--lang',
        help='Specify the language'
    )

    parser.add_argument(
        '--cflags',
        metavar='FLAGS',
        help='Specify compiler flags'
    )

    parser.add_argument(
        '-a', '--args',
        metavar='ARGV',
        nargs='+',
        help='Specify the command-line arguments'
    )

    parser.add_argument(
        '--stdin',
        nargs='+',
        help='Specify the command-line STDIN'
    )

    parser.add_argument(
        '-e', '--exec',
        action='store_true',
        help='Execute the code'
    )

    parser.add_argument(
        '-s', '--skip-asm',
        action='store_true',
        help='Don\'t show the generated assembly'
    )

    parser.add_argument(
        '-C', '--compare',
        action='store_true',
        help='Compare the source code with the assembly'
    )

    parser.add_argument(
        '-L', '--link',
        action='store_true',
        help='Generate a link for the compilation state'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show additional details'
    )

    parser.add_argument(
        'file',
        nargs='?',
        metavar='FILE',
        type=argparse.FileType('r'),
        help='File containing the source code'
    )

    args = parser.parse_args(argv)

    # initialize colorama
    init()

    api.set_host(args.host)

    if args.list_langs:
        list_languages()
    elif args.list_compilers is not False:
        list_compilers(args.list_compilers)
    else:
        file = args.file
        if not file:
            die('No input file')

        compiler = args.compiler
        lang = args.lang
        skip_asm = args.skip_asm
        execute = args.exec
        cflags = args.cflags
        argv = args.args
        stdin = args.stdin
        compare = args.compare
        link = args.link
        verbose = args.verbose

        if stdin:
            stdin = '\n'.join(stdin)

        # try to get the default compiler if none was given
        if not compiler:
            if lang:
                compiler = get_compiler_by_lang(lang)
            else:
                compiler = get_compiler_by_file_ext(file.name)

            if not compiler:
                die('Could not determine the default compiler')

        src = file.read()
        file.close()

        # perform the compilation
        try:
            result = api.compile_src(
                src,
                compiler,
                lang,
                cflags,
                argv,
                stdin,
                skip_asm,
                execute
            )
        except cexpl.NotFoundError:
            die(f'Compiler {compiler} not found')
        except cexpl.CexplError:
            die('Failed to compile')

        if verbose:
            info(f'Using the {compiler} compiler')
            options = ' '.join(result['compilationOptions'])
            info(f'Compilation options:{Fore.RESET} {options}')

        # show the generated link
        if link:
            try:
                link_result = api.generate_short_link(
                    src,
                    compiler,
                    lang,
                    cflags,
                    argv,
                    stdin,
                    execute
                )
            except cexpl.CexplError:
                die('Cannot generate the link')

            url = link_result['url']
            info(f'URL:{Fore.RESET} {url}')

        # show the generated assembly
        if not skip_asm:
            process_asm(result['asm'], src, compare)

        # show stdout/stderr
        process_output(result, execute, verbose)

def list_languages():
    """List available languages"""
    try:
        langs = api.get_languages(fields=['id', 'name'])
    except cexpl.CexplError:
        die('Could not list the available languages')

    # sort languages by id
    langs.sort(key=operator.itemgetter('id'))

    for lang in langs:
        print(f'{Fore.GREEN}{lang["id"]}{Fore.RESET} - {lang["name"]}')

def list_compilers(name):
    """List available compilers"""
    try:
        compilers = api.get_compilers(name, fields=['id', 'name'])
    except cexpl.CexplError:
        die('Could not list the available compilers')

    # sort compilers by id
    compilers.sort(key=operator.itemgetter('id'))

    for compiler in compilers:
        print(f'{Fore.GREEN}{compiler["id"]}{Fore.RESET} - {compiler["name"]}')

def process_asm(asm_result, src, compare=False):
    """Process asm and compare it to src if necessary"""
    if compare:
        lines = src.split('\n')
        prev_line = -1
        for asm in asm_result:
            if asm['source']:
                line = asm['source']['line']
                if line and line != prev_line:
                    code = lines[line - 1].strip()
                    print(f'{line} {Fore.GREEN}{code}{Fore.RESET}')
                    prev_line = line
            print(asm["text"])
    else:
        for asm in asm_result:
            print(asm['text'])

def process_output(result, execute, verbose):
    """Process stdout and stderr streams results"""
    if execute:
        execute_result = result['execResult']
        build_result = execute_result['buildResult']

        if verbose:
            show_output(result['stdout'], result['stderr'])
            info(f'ASM generation compiler returned:{Fore.RESET} {result["code"]}')

            show_output(
                build_result.get('stdout', []),
                build_result.get('stderr', [])
            )
            info(f'Execution build compiler returned:{Fore.RESET} {build_result["code"]}')

            if execute_result['didExecute']:
                show_output(execute_result['stdout'], execute_result['stderr'])
                info(f'Program returned:{Fore.RESET} {execute_result["code"]}')
        else:
            stdout = result['stdout'] + build_result.get('stdout', [])
            stderr = result['stderr'] + build_result.get('stderr', [])

            if execute_result['didExecute']:
                stdout += execute_result['stdout']
                stderr += execute_result['stderr']

            show_output(stdout, stderr)
    else:
        show_output(result['stdout'], result['stderr'])
        if verbose:
            info(f'Compiler returned:{Fore.RESET} {result["code"]}')

def show_output(stdout, stderr):
    """Show stdout and stderr streams"""
    if stdout:
        info('STDOUT:')
        for line in stdout:
            print(line['text'])

    if stderr:
        info('STDERR:')
        for line in stderr:
            print(line['text'])

def get_compiler_by_lang(language):
    """Get the default compiler for a language"""
    try:
        langs = api.get_languages(fields=['id', 'defaultCompiler'])
    except cexpl.CexplError:
        die('Could not get the list of available languages')

    for lang in langs:
        if lang['id'] == language:
            return lang['defaultCompiler']

    return None

def get_compiler_by_file_ext(filename):
    """Get the default compiler based on the file extension"""
    ext = os.path.splitext(filename)[1]
    if not ext:
        return None

    # don't look for C++ compilers when the extension is .c
    if ext == '.c':
        return get_compiler_by_lang('c')

    try:
        langs = api.get_languages(
            fields=['name', 'extensions', 'defaultCompiler']
        )
    except cexpl.CexplError:
        die('Could not get the list of available languages')

    # filter languages that have the same file extension
    langs = list(filter(lambda lang: ext in lang['extensions'], langs))

    if not langs:
        return None

    if len(langs) > 1:
        print(f'Default compilers for {ext} extension:\n')

        for lang in langs:
            compiler = lang['defaultCompiler']
            print(f'{Fore.GREEN}{compiler}{Fore.RESET} - {lang["name"]}')

        compiler = input('\nChoose one compiler: ')

        return compiler

    return langs[0]['defaultCompiler']

def info(string):
    """Print a info message"""
    print(f'{Fore.YELLOW}{string}{Fore.RESET}')

def die(string):
    """Print a message to stderr and exit with failure"""
    print(f'{Fore.RED}{string}{Fore.RESET}', file=sys.stderr)
    sys.exit(1)
