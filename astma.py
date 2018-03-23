#The MIT License

#Copyright (c) 2017 Andreas Wölfl

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import os
import traceback

#--- change input folder ---
folder = ''
#---------------------------

var_name = ''
var_type = ''
var_init = ''
stack = []
dest = []
cnt = 0

def read_folder(path):
    for root, dirs, files in os.walk(path):
        in_path = root.split('/')
        print((len(in_path) - 1) * '---', os.path.basename(root))
            for file in files:
                print(len(in_path) * '---', os.path.join(root, file))
                vars = read_source(os.path.join(root, file))
                replace_source("/".join(in_path), "/".join(in_path), file, vars)
                print(vars)


def replace_source(in_path, out_path, file, vars):
    with open(os.path.join(in_path, file), "r", encoding="utf-8") as src_file:
        src = src_file.read()
        src_removed = remove_comments(src)

        for var in vars:
            for_stmt = 'for '+var[0]+' use at'

            if for_stmt in src:
                idx1 = src_removed.find(for_stmt)
                idx2 = src_removed.find(";",idx1)

            else:
                idx1 = src_removed.find('\t'+var[0]+' : '+var[1])
                if idx1 == -1:
                    idx1 = src_removed.find('\t'+var[0]+' : constant '+var[1])
                    if idx1 == -1:
                        idx1 = src_removed.find(var[0]+' : '+var[1])
                        if idx1 == -1:
                            idx1 = src_removed.find(var[0]+' : constant '+var[1])
                            if idx1 == -1:
                                idx1 = src_removed.find(var[0])
                idx2 = src_removed.find(";",idx1)
            var_src = src_removed[idx1:idx2+1]
            src = src.replace(var_src, var_src+"\n"+instrument(file, var[0]), 1)
        with open(os.path.join(out_path, file), "w+", encoding="utf-8") as dest_file:
            dest_file.seek(0)
            if not 'Memory_Analyzer' in file:
                dest_file.write("with Memory_Analyzer;\n")
            dest_file.write(src)
            dest_file.close()



def read_source(file):
    vars = []
    stack.clear()
    spec = ".ads" in file
    with open(file, "r", encoding="utf-8") as src_file:
        try:
            src = src_file.read()
            src_removed = remove_comments(src)
            i = 0
            tokens = src_removed.split()
            for token in tokens:
                process_token(tokens, i, spec, vars)
                i += 1
        except Exception:
            print('error in '+file)
            print(traceback.format_exc())
    return vars

def process_token(tokens, i, is_spec, vars):

    global stmt_buf
    global var_name
    global var_type
    global var_init
    global stack

    token = tokens[i]
    eof = False

    if ';' in token:
        token = token[0:token.find(';')]
        eof = True

    if token == 'function':
        stack.append(token)
    elif token == 'generic':
        stack.append(token)
    elif token == 'procedure':
        if in_generic():
            stack.pop()
        stack.append(token)
    elif token == 'package':
        if not (tokens[i+2] == 'is' and tokens[i+3] == 'new'):
            stack.append(token)
    elif token == 'record' and not eof:
        stack.append(token)
    elif token == 'declare':
        stack.append(token)
    elif token == 'type':
        stack.append(token)
    elif token == 'subtype':
        stack.append(token)
    elif token == 'begin':
        stack.append(token)
    elif token == 'end':
        if len(tokens) > 1 and ((not 'if' in tokens[i+1])
                                and (not 'loop' in tokens[i+1])
                                and (not 'case' in tokens[i+1])):
            stack.pop()
            if len(stack) > 0 and (not in_package() and not in_local_scope()):
                stack.pop()
    elif is_spec and (in_function() or in_procedure()) and '(' in token:
        stack.append('(')
    elif is_spec and (in_function() or in_procedure()) and ')' in token:
        stack.pop()
        if eof and is_spec and (in_function() or in_procedure()):
            stack.pop()
    elif (in_type() or in_subtype()) and '(' in token and ')' not in token:
        stack.append('(')
    elif (in_type() or in_subtype()) and ')' in token and '(' not in token:
        stack.pop()
        if eof and (in_type()):
            stack.pop()
    elif eof and (in_type() or in_subtype()):
        stack.pop()
    elif eof and is_spec and (len(stack) > 0 and
                                  (stack[len(stack)-1] == 'procedure'
                                  or stack[len(stack)-1] == 'function')):
        stack.pop()
    else:

        if is_variable(tokens,i):
            var_name = token
            if tokens[i+2] != 'constant':
                var_type = tokens[i+2]
            else:
                var_type = tokens[i+3]

            if not 'exception' in var_type and not ':=' in var_type:
                vars.append((var_name, var_type))

    dest.append(token)



def in_local_scope():
    return len(stack) > 0 and stack[len(stack)-1] == 'begin'


def in_package():
    return len(stack) > 0 and stack[len(stack)-1] == 'package'


def in_generic():
    return len(stack) > 0 and stack[len(stack)-1] == 'generic'


def in_procedure():
    return (len(stack) > 0 and stack[len(stack)-1] == 'procedure') or \
           (len(stack) > 1 and (stack[len(stack)-1] ==
           '(' and stack[len(stack)-2] == 'procedure'))


def in_function():
    return len(stack) > 0 and stack[len(stack)-1] == 'function' or \
           (len(stack) > 1 and (stack[len(stack)-1] ==
           '(' and stack[len(stack)-2] == 'function'))


def in_type():
    return len(stack) > 0 and stack[len(stack)-1] == 'type' or \
           (len(stack) > 1 and (stack[len(stack)-1] ==
           '(' and stack[len(stack)-2] == 'type'))


def in_subtype():
    return len(stack) > 0 and stack[len(stack)-1] == 'subtype' or \
           (len(stack) > 1 and (stack[len(stack)-1] ==
           '(' and stack[len(stack)-2] == 'subtype'))


def in_record():
    return len(stack) > 0 and stack[len(stack)-1] == 'record' or \
           (len(stack) > 1 and (stack[len(stack)-1] ==
           '(' and stack[len(stack)-2] == 'record'))


def is_variable(tokens, i):
    return len(tokens) > i+1 and (in_package() or
    in_generic()) and tokens[i+1] == ':'


def is_end_record(tokens, i):
    return len(tokens) > i+1 and in_package() and tokens[i+1] == ':'


def remove_comments(src):
    while src.find('--') != -1:
        idx1 = src.find('--')
        idx2 = src.find('\n', idx1)

        c = src[idx1:idx2+1]

        a = src[0:idx1]
        b = src[idx2+1:]

        rmv = a+b
        src = rmv
    return src


def instrument(fileName, var):
    global cnt
    cnt += 1
    fileName = '"'+fileName+'"'

    s = var + '\'Size'
    if var == 'Byte_Array':
        s = 'Integer(Size_Used)'

    return '   Memory_'+str(cnt)+' : Boolean := Memory_Analyzer.Count' \
                                 '(Size => '+s+', File => '+
                                 fileName+', Var => "'+var+'");'


read_folder(folder)
