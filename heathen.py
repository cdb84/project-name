import subprocess, sys, os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer, cgi, ssl, time
'''
BASIC OPERATIONAL FUNCTIONS

Given a relative path, return the absolute path.
'''
def get_abs_path(local):
    return os.path.realpath(local)
'''
Execute the program denoted by cmd[0], sending in cmd[1:] as args
'''
def execute(args):
    output = ""
    #Test starting the process
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError:
        #Return with failure (typically can't find file)
        return str("404: "+str(sys.exc_info()))
    #pipe the input in and return it to the caller
    for stdout in iter(process.stdout.readline, ""):
        output += stdout
    for stderr in iter(process.stderr.readline, ""):
        output += stderr
    process.wait()
    return process_output
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
INLINE_EXT = ".inl"
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
def module_compile(module_count, inline_sourcep, compiler_string, inlines):
    #we will write to the following file to contain the source from the inlines
    inline_module_srcfilep = (inline_filep
                                       +MODULES_SUBDIRECTORY
                                       +str(module_count))
    #we will pipe the following to the compiler string to see that the
    #output filepath equals this string
    inline_module_extfilep = (inline_filep
                                       +MODULES_SUBDIRECTORY
                                       +str(module_count)+MODULE_EXT)
    compiler_string = compiler_string.replace(INPUT, inline_module_srcfilep)
    compiler_string = compiler_string.replace(OUTPUT, inline_module_extfilep)
    args = compiler_string.split(" ")
    #we gotta create the source for this module
    with open(inline_module_srcfilep, 'w') as source:
        source.write(inlines)
    #now compile that file we just wrote using the source-defined compiler
    #string
    return exec_helper(args)
def serve_inline(inline_filep):
    return serve_inline(inline_filep, [])
'''
Generates a response from an inline file; this funcion will attempt the 
following:
  A) to execute the modules specified by the inline file
  B) to compile new modules if it is determined that the modules for this 
  inline file are too old
  C) to compile new modules if they don't exist
  D) to run these newly compiled modules
'''
def serve_inline(inline_filep, args):
    response = ""
    #try/except in case this file does not exist, etcetera
    try:
        compiler_string, inlines = ""
        record = False
        module_count, inline_file_time = 0
        #we're gonna scan through the file and take it line by line to
        #determine where the inline portion is, and how it is compiled.
        with open(inline_filep, 'r') as i:
            this_line = i.readline()
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
            if record and not INLINE_FLAG in this_line:
                inlines += this_line
        #TEST HERE FOR IF THE MODULE EXISTS AND HAS A COMPILE DATE OLDER
        #THAN THE SOURCE .inl FILE
        inline_file_time = os.stat(inline_filep).st_mtime            
        for i in module_count:
            try:
                inline_module_extfilep = (inline_filep
                                       +MODULES_SUBDIRECTORY
                                       +str(module_count)+MODULE_EXT)
                #record the time of this particular module file
                inline_module_exec_time = os.stat(
                    inline_module_extfilep).st_mtime
                #compare it to the original inline source file
                if inline_file_time > inline_module_exec_time:
                    #recompile this module
                    #execute this module, append output to response
                    module_compile(i, inline_filep, compile_string, inlines)
                else:
                    #execute the module, since it is apparently newly compiled
                    #as compared to the inline source's modification time
                    #also, accomodate for arguments sent via POST
                    args.insert(0, inline_module_extfilep)
                    response += exec_helper(args)
            except:
                #assume the file does not exist, compile a new one!
                #compile this module, append output to response
                module_compile(i, inline_filep, compile_string, inlines)
                args.insert(0, inline_module_extfilep)
                response += exec_helper(args)

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
            self.wfile.write(exec_helper(hard_path))
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
        #insert the executable at the top of the list
        arguments.insert(0, hard_path)
        #execute the entire list of arguments
        #this is where the security vulnerabillity is most promoinent
        #as by altering the form/POST data, one could arguably execute
        #any arbitrary program that the webserver itself could execute
        self.wfile.write(exec_helper(arguments))
def run(server_class=HTTPServer, handler_class=SpecialPreprocessor, port=80):
    httpd = server_class(('', port), handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

def run_ssl(server_class=HTTPServer, handler_class=SpecialPreprocessor,
            port=443, certificate=''):
    httpd = server_class(('', port), handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=CERTIFICATE,
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

