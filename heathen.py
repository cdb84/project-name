#/usr/bin/python
"""
Heathen Webserver: a webserver that does back-end preprocessing in whatever
language you want, be it C, Fortran, or Assembly.
"""
import subprocess
import sys
import os
import cgi
import ssl
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
DEFAULT_MIMETYPE = "text/plain"
MIMETYPES = {
    "html":"text/html",
    "jpg":"image/jpg",
    "gif":"image/gif",
    "png":"image/png",
    "svg":"image/svg+xml",
    "js":"application/javascript",
    "css":"text/css",
    "mp4":"video/mp4",
    "webm":"video/webm",
    "wav":"audio/wav"
    }
"""
BASIC OPERATIONAL FUNCTIONS
"""
def execute(cmd_args):
    """
    Execute the program denoted by cmd[0], sending in cmd[1:] as args
    """
    output = ""
    #Test starting the process
    try:
        process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError:
        #Return with failure (typically can't find file)
        return str("404: "+str(sys.exc_info()))
    #Pipe the output and return it to the caller
    for stdout in iter(process.stdout.readline, ""):
        output += stdout
    #Arguable risk in piping out stderr as well and returning it to the client
    for stderr in iter(process.stderr.readline, ""):
        output += stderr
    process.wait()
    return output
def read_file(path):
    """
    Read a text file line by line; returns those lines compounded into a string
    """
    response = ""
    #Try opening the file
    try:
        with open(path, 'r+b') as i:
            response += i.read()
    except:
        #Return the exception
        response = str("500: "+str(sys.exc_info()))
    #Return that compounded string from the file.
    return response
def present_in(needle, trup_haystack, index):
    """
    Returns true if needle exists in the 'index' position of the truple haystack
    """
    for i in trup_haystack:
        if i[index] is needle:
            return True
    return False
def get_mimetype(path):
    """
    Returns a string describing the mimetype of the given filepath.
    """
    ext = path.split(".")[-1]
    try:
        return MIMETYPES[ext]
    except KeyError:
        return DEFAULT_MIMETYPE
INDEX = "index.html"
EXECUTABLE_EXT = ".out"
INLINE_EXT = ".hea"
MODULE_EXT = ".mod"
INLINE_FLAG = "$$"
INPUT = "INPUT"
OUTPUT = "OUTPUT"
COMPILER_STRING_SIG = "'"
MODULES_SUBDIRECTORY = "_modules/"
NO_COMPILE_SIG = "DO NOT COMPILE"
"""
COMPLEX SERVING FUNCTIONS
"""
def post_args_from_form(form):
    """
    Take a table of form data or other sort of dictionary and turn it into a
    regular 1D list to be passed as args
    """
    res = list()
    for item in form:
        res.append(item)
        res.append(form[item].value)
    return res
def get_compiler_string(line):
    """
    Scans a string to see if it can determine a compiler directive based on pre-
    defined signage
    """
    result = ""
    record = False
    #Examine every character in the line
    for character in line:
        #If the current character flags a compiler direction
        if character is COMPILER_STRING_SIG:
            #Record will equal it's contra--if we just found this, we start
            #recording. If we already were recording, it will stop recording
            record = not record
        #And thus, our condition to record these characters as compiler string
        #Don't want to take the compiler sign with us
        if record and character is not COMPILER_STRING_SIG:
            result += character
    return result
def get_ext(compiler_string):
    """
    Strip INPUT off the compiler string and see which file extension follows the
    INPUT flag; returns that. E.g. 'gcc INPUT.c' -> '.c'
    """
    psplit = compiler_string.split(" ")
    for item in psplit:
        if INPUT in item:
            return item.replace(INPUT, "")
    return ""
def module_compile(module_no, inline_sourcep, inlines_struct):
    """
    Compile a module of an inline webpage.
    module_no = which module this is in the webpage. This index starts at 1,
    unfortunately.
    inline_sourcep = the path to the inline file
    inlines_struct = a truple structure containing the following:
      (module_index, compiler_string, actual line of code)
    """
    compiler_string = inlines = ""
    #Extrapolate data from the truple
    for i in inlines_struct:
        if i[0] is module_no:
            compiler_string = i[1]
            inlines += i[2]
    #Hopefully we can at some point incorporate interpreted languages such as
    #python, bash, etc
    if compiler_string is NO_COMPILE_SIG:
        return ""
    subdirectory = inline_sourcep+MODULES_SUBDIRECTORY
    src_ext = get_ext(compiler_string)
    #We will write to the following file to contain the source from the inlines
    inline_module_srcfilep = (inline_sourcep
                              +MODULES_SUBDIRECTORY
                              +str(module_no)+src_ext)
    #We will pipe the following to the compiler string to see that the
    #output filepath equals this string
    inline_module_extfilep = (inline_sourcep
                              +MODULES_SUBDIRECTORY
                              +str(module_no)+MODULE_EXT)
    compiler_string = compiler_string.replace(INPUT+src_ext,
                                              inline_module_srcfilep)
    compiler_string = compiler_string.replace(OUTPUT, inline_module_extfilep)
    post_args = compiler_string.split(" ")
    #We must create the source for this module
    #This crashes if there isn't a modules directory to look into
    if not os.path.exists(subdirectory):
        os.makedirs(subdirectory)
    with open(inline_module_srcfilep, 'w') as source:
        source.write(inlines)
    #Now compile that file we just wrote using the source-defined compiler
    #string
    return execute(post_args)
def serve_inline(inline_filep, post=None):
    """
    Generates a response from an inline file; this funcion will attempt the
    following:
      A) to execute the modules specified by the inline file
      B) to compile new modules if it is determined that the modules for this
      inline file are too old
      C) to compile new modules if they don't exist
      D) to run these newly compiled modules
    """
    #Apparently this is the safesty way to default a blank list
    if post is None:
        post = []
    response = ""
    #Try/except in case this file does not exist, etcetera
    try:
        compiler_string = ""
        inlines = []
        record = False
        #At some point, the modules is treated like an array that starts at
        #1. I am so sorry about this, but it makes sense in this context as
        #module_count must be 0 to indicate no modules.
        module_count = inline_file_time = 0
        #We're gonna scan through the file and take it line by line to
        #determine where the inline portion is, and how it is compiled.
        with open(inline_filep, 'r') as i:
            lines = i.readlines()
        for this_line in lines:
            if INLINE_FLAG in this_line:
                #Switch record flag
                record = not record
                #If record has just recently been switched to true, record:
                if record:
                    #Which module this is
                    module_count += 1
                    #Which compiler string to use
                    compiler_string = get_compiler_string(this_line)
            #Don't take any lines with the damn inline flag in it
            if record and INLINE_FLAG not in this_line:
                #Inline record for module module_count; truples oh boy
                inlines.append((module_count, compiler_string, this_line))
        #For efficiency's sake, we should compare times of compilation to
        #see if we can save a step
        inline_file_time = os.stat(inline_filep).st_mtime
        #Loop for every module in the inline file
        for i in range(1, module_count+1):
            try:
                #Create the module filename
                inline_module_extfilep = (inline_filep
                                          +MODULES_SUBDIRECTORY
                                          +str(i)+MODULE_EXT)
                #Record the time of this particular module executable
                inline_module_exec_time = os.stat(
                    inline_module_extfilep).st_mtime
                #Compare it to the original inline source file
                if inline_file_time > inline_module_exec_time:
                    #Recompile this module
                    #Printing sends compilation errors to console
                    print module_compile(i, inline_filep, inlines)
            except OSError:
                #Assume the file does not exist, compile a new one
                #Printing sends compilation errors to console
                print module_compile(i, inline_filep, inlines)
        #Keep track of which module we're on
        module_index = 0
        #Which inline of the actual source file are we serving
        lindex_inline = 0
        for this_line in lines:
            #Serving a regular line of html/text
            if (not present_in(this_line, inlines, 2)
                    and INLINE_FLAG not in this_line):
                response += this_line
                #Reset the inline line index
                if lindex_inline > 0:
                    lindex_inline = 0
            #Else, we have to serve the executable's output only if this is the
            #first inline line we've encountered. All others are skipped.
            elif lindex_inline is 0:
                #Increment this so that we don't keep serving the same
                #executable for every line of inline code
                lindex_inline += 1
                temp_post = post
                module_index += 1
                inline_module_extfilep = (inline_filep
                                          +MODULES_SUBDIRECTORY
                                          +str(module_index)+MODULE_EXT)
                temp_post.insert(0, inline_module_extfilep)
                response += execute(temp_post)
    except:
        response += str("500: "+str(sys.exc_info()))
    return response
class SpecialPreprocessor(BaseHTTPRequestHandler):
    """
    Our tailored request handler. GET behaves fairly expectedly, however POST
    is sorta hacky. Most of these methods have the pretense of executing other
    programs written in other languages in the same webroot directory as the 
    server.
    """
    def _set_headers(self, mimetype="text/html"):
        """
        Run of the mill headers, they get sent for every request. Always 200,
        'text/html' mimetype. This function will be changed later to serve
        different mimetypes.
        """
        self.send_response(200)
        self.send_header("Content-type", mimetype)
        self.end_headers()

    def do_GET(self):
        """
        This GET method compares the extension of the request path, to see if it
        refers to a file that implies preprocessing/executables.
        """
        #Need to use absolute paths for some odd reason
        hard_path = os.path.realpath(self.path[1:])
        #Show index for GET '/'
        if self.path is '/':
            self._set_headers() #'text/html' mimetype for these text options
            self.wfile.write(read_file(INDEX))
        #Otherwise execute something if path ends with .out
        elif self.path.endswith(EXECUTABLE_EXT):
            self._set_headers() 
            self.wfile.write(execute(hard_path))
        elif self.path.endswith(INLINE_EXT):
            self._set_headers() 
            self.wfile.write(serve_inline(hard_path))
        #Otherwise pipe whatever file is being requested
        else:
            self._set_headers(mimetype=get_mimetype(self.path))
            self.wfile.write(read_file(hard_path))
    def do_HEAD(self):
        """
        Headers response. Nothing really special here.
        """
        self._set_headers()
    def do_POST(self):
        """
        POST requests are handled differently than GET. POST will pipe the
        POST form into the compiled executable as a 1 dimmensional array.
        """
        self._set_headers()
        #Take hard path again because *NIX trivialities
        hard_path = os.path.realpath(self.path[1:])
        #Create the POST form object
        environment = {'REQUEST_METHOD':'POST',
                       'CONTENT_TYPE':self.headers['Content-Type'],}
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                environ=environment)
        #Cast those arguments into a list
        arguments = post_args_from_form(form)
        if self.path.endswith(EXECUTABLE_EXT):
            #Otherwise execute something if path ends with .out
            arguments.insert(0, hard_path)
            self.wfile.write(execute(arguments))
        #Take the inline route and send in the POST data along with it
        elif self.path.endswith(INLINE_EXT):
            self.wfile.write(serve_inline(hard_path, post=arguments))
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    A class to handle threading. Very hands-off, apparently.
    """

def run(server_class=ThreadedHTTPServer, handler_class=SpecialPreprocessor,
        port=80):
    """
    Run an instance of the webserver with unsecured HTTP.
    """
    httpd = server_class(('', port), handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

CERTIFICATE_P = "server.crt"
def run_ssl(server_class=ThreadedHTTPServer, handler_class=SpecialPreprocessor,
            port=443, certificate=CERTIFICATE_P):
    """
    Run an instance of the webserver with socketed HTTPS.
    """
    httpd = server_class(('', port), handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=certificate,
                                   server_side=True)
    print 'Starting httpd...'
    httpd.serve_forever()

if __name__ == "__main__":
    import argparse
    clparser = argparse.ArgumentParser(description="Heathen Webserver: a"+
                                       " ridiculously dangerous webserver that"+
                                       " allows preprocessing to any executable")
    clparser.add_argument("-port", help="The port to bind to.", type=int)
    clparser.add_argument("-ssl",
                          help="Use SSL/HTTPS; specify the certificate.",
                          type=int)
    sysargs = clparser.parse_args()
    if sysargs.port and sysargs.ssl:
        run_ssl(port=sysargs.port, certificate=sysargs.ssl)
    elif sysargs.ssl:
        run_ssl(certificate=sysargs.ssl)
    elif sysargs.port:
        run(port=sysargs.port)
    else:
        run()
