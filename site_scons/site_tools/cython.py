import os
import re
import shlex
import subprocess

from SCons.Scanner import FindPathDirs
from SCons.Script import Action, Builder


def exists(env):
    return env.Detect('cython')


def generate(env):
    env.Tool('python')

    env.SetDefault(CYTHONPATH=[])

    env['BUILDERS']['Cython'] = Builder(
        action=Action(
            cython_build_action,
            strfunction=cython_build_strfunction,
        ),
        suffix='.cpp',
        src_suffix='.pyx',
    )

    scanner = env.Scanner(
        function=cython_scan,
        skeys=['.pyx', '.pyd', '.pyi'],
        path_function=lambda *args: (
            FindPathDirs('PYTHONPATH')(*args)
            + FindPathDirs('CYTHONPATH')(*args)
        ),
        recursive=True,
    )

    env.Append(SCANNERS=scanner)


def cython_build_action(target, source, env):
    try:
        subprocess.check_call(cython_build_command(target, source, env))
    except subprocess.CalledProcessError:
        if os.path.isfile(target[0].abspath):
            os.remove(target[0].abspath)
        return 1


def cython_build_strfunction(target, source, env):
    if getattr(shlex, 'join', None):
        return shlex.join(cython_build_command(target, source, env))
    else:
        # XXX: For Python 3.6 compatibility.
        return ' '.join(shlex.quote(s) for s in cython_build_command(target, source, env))


def cython_build_command(target, source, env):
    flags = ['-3']
    flags += ['-I' + str(p) for p in env['CYTHONPATH']]

    if target[0].get_suffix() == '.cpp':
        flags.append('--cplus')

    return [
        env.subst('$PYTHON'),
        '-m',
        'cython',
        *flags,
        '-o',
        *env.subst(['$TARGET', '$SOURCE'], target=target, source=source),
    ]


def cython_scan(node, env, path):
    deps = []

    contents = node.get_text_contents()
    cimports, includes, externs = extract_dependencies(contents)

    for cimport in cimports:
        dep = find_pdx(cimport, node, env, path)
        if dep is not None:
            deps += dep

    for include in includes:
        dep = env.FindFile(include, path)
        if dep is not None:
            deps.append(dep)

    return deps


def find_pdx(modulename, imported_from, env, search_dirs):
    *parents, base = modulename.split('.')

    if parents and parents[0] == '':
        path = imported_from
        i = 0
        for i, package in enumerate(parents):
            if package != '': break
            path = path.Dir('..')
        return find_pdx_in_dir('.'.join([*parents[i:], base]), env, path)

    for path in search_dirs:
        deps = find_pdx_in_dir(modulename, env, path)
        if deps:
            break
    else:
        return []
    
    return deps


def find_pdx_in_dir(modulename, env, directory):
    deps = []

    *parents, base = modulename.split('.')
    if base == '':
        return None

    path = directory

    if len(parents) > 1:
        for p in parents[:-1]:
            next_path = path.Dir(p)
            if next_path.exists():
                path = next_path
                package = env.FindFile('__init__.pxd', path)
                if package is not None:
                    deps.append(package)
            else:
                return []
    
    if len(parents) > 0:
        next_path = path.Dir(parents[-1])
        if next_path.exists():
            package = env.FindFile('__init__.pxd', next_path)
            if package is not None:
                deps.append(package)
            path = next_path
        else:
            module = env.FindFile(parents[-1] + '.pxd', next_path)
            if module is not None:
                deps.append(module)
            return deps

    module = env.FindFile(base + '.pxd', path)
    if module is not None:
        deps.append(module)

    return deps


# Taken from Cython codebase.
dependency_regex = re.compile(
    r"(?:^\s*from +([0-9a-zA-Z_.]+) +cimport)|"
    r"(?:^\s*cimport +([0-9a-zA-Z_.]+(?: *, *[0-9a-zA-Z_.]+)*))|"
    r"(?:^\s*cdef +extern +from +['\"]([^'\"]+)['\"])|"
    r"(?:^\s*include +['\"]([^'\"]+)['\"])",
    re.M
)


dependency_after_from_regex = re.compile(
    r"^"
    r"(?:\\\n|[^S\n]*)*"
    r"\((\s*"

    r"(?:"
    + r"[^()\\\n]*"
    + r"\s*(?:\s*#.*|\s*\\\n)*\s*"  # Line continuation or comment.
    + r","
    + r"\s*(?:\s*#.*|\s*\\\n)*\s*"
    r")*"

    r"(?:"
    + r"[^()\\\n]*"
    + r"\s*(?:\s*#.*|\s*\\\n)*"
    r")?"

    r"\s*)\)"

    r"|"

    r"^((?:[^()\\\n]*(?:\\\n))*(?:[^()\\\n]*(?:\n|$)))"
)

# Taken from Cython codebase.
def extract_dependencies(code):
    source, literals = escape_string_literals(code)
    source = source.replace('\\\n', ' ').replace('\t', ' ')
    
    cimports = []
    includes = []
    externs  = []
    for m in dependency_regex.finditer(source):
        cimport_from, cimport_list, extern, include = m.groups()
        if cimport_from:
            cimports.append(cimport_from)
            m_after_from = dependency_after_from_regex.search(source[m.end():])
            if m_after_from:
                multi_line, one_line = m_after_from.groups()
                subimports = multi_line or one_line
                # Remove line continuations.
                subimports = subimports.replace('\\', '')
                # Remove comments.
                subimports = re.sub(r"#.*", '', subimports)
                # Remove aliases and split to list.
                subimports = [re.sub("as .*", '', s, re.DOTALL).strip() for s in subimports.split(',')]
                cimports.extend(
                    "{0}.{1}".format(
                        re.sub(r"\.$", '', cimport_from),
                        subimport
                    )
                    for subimport in subimports
                )
        elif cimport_list:
            cimports.extend(x.strip() for x in cimport_list.split(","))
        elif extern:
            externs.append(literals[extern])
        else:
            includes.append(literals[include])

    return cimports, includes, externs


# Taken from Cython codebase.
def escape_string_literals(code, prefix='__Pyx_L'):
    """
    Normalizes every string literal to be of the form '__Pyx_Lxxx_',
    returning the normalized code and a mapping of labels to
    string literals.
    """
    new_code = []
    literals = {}
    counter = 0
    start = q = 0
    in_quote = False
    hash_mark = single_q = double_q = -1
    code_len = len(code)
    quote_type = None
    quote_len = -1

    while True:
        if hash_mark < q:
            hash_mark = code.find('#', q)
        if single_q < q:
            single_q = code.find("'", q)
        if double_q < q:
            double_q = code.find('"', q)
        q = min(single_q, double_q)
        if q == -1:
            q = max(single_q, double_q)

        # We're done.
        if q == -1 and hash_mark == -1:
            new_code.append(code[start:])
            break

        # Try to close the quote.
        elif in_quote:
            if code[q-1] == u'\\':
                k = 2
                while q >= k and code[q-k] == u'\\':
                    k += 1
                if k % 2 == 0:
                    q += 1
                    continue
            if code[q] == quote_type and (
                    quote_len == 1 or (code_len > q + 2 and quote_type == code[q+1] == code[q+2])):
                counter += 1
                label = "%s%s_" % (prefix, counter)
                literals[label] = code[start+quote_len:q]
                full_quote = code[q:q+quote_len]
                new_code.append(full_quote)
                new_code.append(label)
                new_code.append(full_quote)
                q += quote_len
                in_quote = False
                start = q
            else:
                q += 1

        # Process comment.
        elif -1 != hash_mark and (hash_mark < q or q == -1):
            new_code.append(code[start:hash_mark+1])
            end = code.find('\n', hash_mark)
            counter += 1
            label = "%s%s_" % (prefix, counter)
            if end == -1:
                end_or_none = None
            else:
                end_or_none = end
            literals[label] = code[hash_mark+1:end_or_none]
            new_code.append(label)
            if end == -1:
                break
            start = q = end

        # Open the quote.
        else:
            if code_len >= q+3 and (code[q] == code[q+1] == code[q+2]):
                quote_len = 3
            else:
                quote_len = 1
            in_quote = True
            quote_type = code[q]
            new_code.append(code[start:q])
            start = q
            q += quote_len

    return "".join(new_code), literals
