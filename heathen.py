import subprocess, sys, os
CERTIFICATE="path/to/crt"
'''
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
        #Return with failure 
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
    #try opening the file 
    try:
        open(path, 'r')
    except:
        #return the exception
        return str("404: "+str(sys.exc_info()))
    response = ""
    #read every line and compile it into a string
    with open( path, 'r' ) as i:
        response += i.read()
    #return that string
    return response
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer, cgi
INDEX = "index.html"
EXECUTABLE_EXT = ".out"
'''
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
Our tailored request handler. GET behaves fairly expectedly, however POST
is sorta hacky.
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
        else:
            #otherwise pipe whatever file is being requested
            #todo: make this work for more than just text/html
            self.wfile.write(read_text_file(hard_path))
    def do_HEAD(self):
        self._set_headers()
        
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
            port=443):
    httpd = server_class(('', port), handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=CERTIFICATE,
                                    server_side=True)
    print 'Starting httpd...'
    httpd.serve_forever()
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Heathen Webserver: a"+
                                     " ridiculously dangerous webserver that"+
                                     " allows preprocessing to any executable")
    parser.add_argument("port", help="The port to bind to.", type=int)
    parser.add_argument("-ssl", help="Use SSL/HTTPS.", action="store_true")
    args = parser.parse_args()
    if args.port and args.ssl:
        run_ssl(port=args.port)
    elif args.ssl:
        run_ssl()
    elif args.port:
        run(port=args.port)
    else:
        run()

