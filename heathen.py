#/usr/bin/python
import subprocess
import sys
import os
import cgi
import ssl
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
'''
BASIC OPERATIONAL FUNCTIONS

Given a relative path, return the absolute path.
'''
def get_abs_path(local):
    return os.path.realpath(local)
'''
Execute the program denoted by cmd[0], sending in cmd[1:] as args
'''
def execute(cmd_args):
    output = ""
    #Test starting the process
    try:
        process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError:
        #Return with failure (typically can't find file)
        #print cmd_args
        return str("404: "+str(sys.exc_info()))
    #pipe the input in and return it to the caller
    for stdout in iter(process.stdout.readline, ""):
        output += stdout
    for stderr in iter(process.stderr.readline, ""):
        output += stderr
    process.wait()
    return output
'''
Read a text file line by line; returns those lines compounded into a string
'''
def read_text_file(path):
    response = ""
    #try opening the file
    try:
        with open(path, 'r') as i:
            response += i.read()
    except:
        #return the exception
        response = str("500: "+str(sys.exc_info()))
    #return that string
    return response


INDEX = "index.html"
EXECUTABLE_EXT = ".out"
INLINE_EXT = ".hea"
MODULE_EXT = ".mod"
INLINE_FLAG = "$$"
INPUT = "INPUT"
OUTPUT = "OUTPUT"
COMPILER_STRING_SIG = "'"
#so when looking for modules, it is hard_path+MODULES_SUBDIRECTORY
MODULES_SUBDIRECTORY = "_modules/"
'''
COMPLEX SERVING FUNCTIONS

Take a table of form data or other sort of dictionary and turn it into a
regular list to be passed as args
'''
def args_from_form(form):
    res = list()
    for item in form:
        res.append(item)
        res.append(form[item].value)
    return res
'''
Scans a string to see if it can determine a compiler directive based on pre-
defined signage 
'''
def get_compiler_string(line):
    result = ""
    record = False
    #examine every character in the line
    for character in line:
        #if the current character flags a compiler direction
        if character is COMPILER_STRING_SIG:
            #record will equal it's contra--if we just found this, we start
            #recording. If we already found this before, it will stop recording
            record = not record
        #and thus, our condition to record these characters as compiler string
        if record and character is not COMPILER_STRING_SIG:
            result += character
    return result
def get_ext(compiler_string):
    psplit = compiler_string.split(" ")
    for item in psplit:
        if INPUT in item:
            return item.replace(INPUT, "")
    return ""
def module_compile(module_no, inline_sourcep, inlines_struct):
    compiler_string = ""
    inlines = ""
    #extrapolate data from the truple
    for i in inlines_struct:
        #print i
        if i[0] == module_no:
            compiler_string = i[1]
            inlines += i[2]
            #print i[0], i[1], i[2]
    subdirectory = inline_sourcep+MODULES_SUBDIRECTORY
    src_ext = get_ext(compiler_string)
    #we will write to the following file to contain the source from the inlines
    inline_module_srcfilep = (inline_sourcep
                              +MODULES_SUBDIRECTORY
                              +str(module_no)+src_ext)
    #we will pipe the following to the compiler string to see that the
    #output filepath equals this string
    inline_module_extfilep = (inline_sourcep
                              +MODULES_SUBDIRECTORY
                              +str(module_no)+MODULE_EXT)
    compiler_string = compiler_string.replace(INPUT+src_ext,
                                              inline_module_srcfilep)
    compiler_string = compiler_string.replace(OUTPUT, inline_module_extfilep)
    post_args = compiler_string.split(" ")
    #we gotta create the source for this module
    #this crashes if there isn't a modules directory to look into
    if not os.path.exists(subdirectory):
        os.makedirs(subdirectory)
    with open(inline_module_srcfilep, 'w') as source:
        source.write(inlines)
    #now compile that file we just wrote using the source-defined compiler
    #string
    return execute(post_args)
def present_in(needle, trup_haystack):
    for i in trup_haystack:
        if i[2] is needle:
            return True
    return False
'''
Generates a response from an inline file; this funcion will attempt the 
following:
  A) to execute the modules specified by the inline file
  B) to compile new modules if it is determined that the modules for this 
  inline file are too old
  C) to compile new modules if they don't exist
  D) to run these newly compiled modules
'''
def serve_inline(inline_filep, args=[]):
    response = ""
    #try/except in case this file does not exist, etcetera
    try:
        compiler_string = ""
        inlines = []
        record = False
        #we will go against better convention here and say that our module
        #list starts at one (I am so sorry)
        module_count = inline_file_time = 0
        #we're gonna scan through the file and take it line by line to
        #determine where the inline portion is, and how it is compiled.
        with open(inline_filep, 'r') as i:
            lines = i.readlines()
        for this_line in lines:
            #this is going to be the hardest part
            if INLINE_FLAG in this_line:
                #switch record flag
                record = not record
                #if record has just recently been switched to true, record:
                if record:
                    #which module this is
                    module_count += 1
                    #which compiler string to use
                    compiler_string = get_compiler_string(this_line)
            #don't take any lines with the damn inline flag in it
            if record and INLINE_FLAG not in this_line:
                #inline record for module module_count; truples oh boy
                inlines.append((module_count, compiler_string, this_line))
        #for efficiency's sake, we should compare times of compilation to
        #see if we can save a step
        inline_file_time = os.stat(inline_filep).st_mtime
        #iterative loop for every module
        for i in range(1, module_count+1):
            try:
                #create the module filename
                inline_module_extfilep = (inline_filep
                                          +MODULES_SUBDIRECTORY
                                          +str(i)+MODULE_EXT)
                #record the time of this particular module executable
                inline_module_exec_time = os.stat(
                    inline_module_extfilep).st_mtime
                #compare it to the original inline source file
                if inline_file_time > inline_module_exec_time:
                    #recompile this module
                    #printing sends errors to console
                    print module_compile(i, inline_filep, inlines)
            except OSError:
                #assume the file does not exist, compile a new one
                #compile this module, append output to response
                #printing sends errors to console
                print module_compile(i, inline_filep, inlines)
        #keep track of which module we're on
        module_index = 0
        #which inline of the actual html file are we serving
        lindex_inline = 0
        for this_line in lines:
            #serving a regular line of html/text
            if (not present_in(this_line, inlines)
                    and INLINE_FLAG not in this_line):
                response += this_line
                #reset the inline line index
                if lindex_inline > 0:
                    lindex_inline = 0
            #we have to serve the executable's output
            elif lindex_inline == 0:
                #increment this so that we don't keep serving the same
                #executable for every line of inline code
                lindex_inline += 1
                temp_post = args
                module_index += 1
                inline_module_extfilep = (inline_filep
                                          +MODULES_SUBDIRECTORY
                                          +str(module_index)+MODULE_EXT)
                temp_post.insert(0, inline_module_extfilep)
                response += execute(temp_post)
    except:
        response += str("500: "+str(sys.exc_info()))
    return response
'''
Our tailored request handler. GET behaves fairly expectedly, however POST
is sorta hacky. Most of these methods have the pretense of executing other
programs written in other languages in the same webroot directory as the server.
'''
class SpecialPreprocessor(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        #need to use absolute paths for some odd reason
        hard_path = get_abs_path(self.path[1:])
        if self.path == '/':
            #show index for GET '/'
            self.wfile.write(read_text_file(INDEX))
        elif self.path.endswith(EXECUTABLE_EXT):
            #otherwise execute something if path ends with .out
            self.wfile.write(execute(hard_path))
        elif self.path.endswith(INLINE_EXT):
            self.wfile.write(serve_inline(hard_path))
        else:
            #otherwise pipe whatever file is being requested
            #todo: make this work for more than just text/html
            self.wfile.write(read_text_file(hard_path))
    def do_HEAD(self):
        self._set_headers()

    #NOTE: POSTing to inlines requires the execution string to the particular
    #module to always carry the POST arguments. We will have to have checks in
    #place for the various filetypes
    def do_POST(self):
        self._set_headers()
        #take hard path again because *NIX trivialities
        hard_path = get_abs_path(self.path[1:])
        #creat the POST form object
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                    }
        )
        #cast those arguments into a list
        arguments = args_from_form(form)
        if self.path.endswith(EXECUTABLE_EXT):
            #otherwise execute something if path ends with .out
            arguments.insert(0, hard_path)
            self.wfile.write(execute(arguments))
        #take the inline route and send in the POST data along with it
        elif self.path.endswith(INLINE_EXT):
            self.wfile.write(serve_inline(hard_path, args=arguments))
def run(server_class=HTTPServer, handler_class=SpecialPreprocessor, port=80):
    httpd = server_class(('', port), handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

def run_ssl(server_class=HTTPServer, handler_class=SpecialPreprocessor,
            port=443, certificate=''):
    httpd = server_class(('', port), handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=certificate,
                                   server_side=True)
    print 'Starting httpd...'
    httpd.serve_forever()
if __name__ == "__main__":
    import argparse
    CERTIFICATE_P = "path/to/crt"
    parser = argparse.ArgumentParser(description="Heathen Webserver: a"+
                                     " ridiculously dangerous webserver that"+
                                     " allows preprocessing to any executable")
    parser.add_argument("port", help="The port to bind to.", type=int)
    parser.add_argument("-ssl", help="Use SSL/HTTPS.", action="store_true")
    args = parser.parse_args()
    if args.port and args.ssl:
        run_ssl(port=args.port, certificate=CERTIFICATE_P)
    elif args.ssl:
        run_ssl()
    elif args.port:
        run(port=args.port)
    else:
        run()
