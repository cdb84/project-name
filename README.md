# heathen-webserver
A webserver I shouldn't have made but still did. On the plus side,
you can do webpage preprocessing in C now.
## This Is Terrifying
You probably shouldn't do this sorta thing, and it doesn't make sense. I 
sorta just did it for the hell of it. Maybe someday I'll find a reason to 
use a systems-side language over:
- PHP
- Node.js
- Flask
- Literally anything else

But for now, Frankenstein project.

## How It Works
### GET
The webserver is specially designed to handle requests of both GET and POST a
particular way. When a GET is received, it compares the ending extension of the
requested path to see if it ends in '.out', our ad-hoc preprocessing file
extension. If it does, the web server then executes that binary (if the mode
of that file is executable) and the output is piped directly to the user in 
the form of a new, preprocessed webpage. *"But isn't that insecure???"* No, not
this part--the web server automatically converts all paths to long-form hard
paths, meaning that it can only execute binaries that are present within the
directory it is serving out of.
### POST
For data that is POSTed to the webserver, this is simply sent in as arguments
to the program and then converted back into a dictionary, similar to the way
PHP handles POST data. This is probably also equally terrible.

## Usage
### Server
`python heathen.py [-port PORT] [-crt Certificate Path] [-key Keyfile Path]`

Note that SSL functionality is not confirmed to work safely.

### Browser
Simply navigate to the webserver's address, and enter the URL of an executable
or .hea file. 
That's all!

### Example files
In the master branch, there exists a few files:

- exec.c and exec.out, which can be called to as an individual executable that
the server can run as a pre-process
- index.html, the index of this webroot. Nothing really special here.
- test.hea, an inline 'heathen' file that you can *write C or Fortran code in to
have preprocessed*:
```
<html>
<head>
</head>
<h1>This is normal html, and sent to the client as such. However, you can do
$$'gcc INPUT.c -o OUTPUT'>
#include <stdio.h>

int main(){
  puts("The following!");
}
$$>
and it works inline!!!</h1>
<p>
$$'gcc INPUT.c -o OUTPUT'>
#include <stdio.h>

int main(){
  puts("In fact, you can do it as many ");
  
}
$$>
times as you wish,
$$'gcc INPUT.c -o OUTPUT'>
#include <stdio.h>
#include <unistd.h>

int main(){
  puts(" it should always work.");
  //sleep(60); this is here as a test of the multithreading
}
$$>
<!--There must be at least one line between modules. Idk why yet.-->
<$$'gfortran INPUT.f90 -o OUTPUT'>
program hello
      implicit none

      WRITE(6,*) 'Hello World!'

end program hello

$$>
</p>
<!--I wish emacs would stop assuming my language.-->
</html>
```
INPUT should specify where in your compiler statement the input file-path
goes, and OUTPUT should specify the output argument positioning.
This is done so that when the webserver live-compiles, it knows what
files and paths to send into the compile statement. The opening and closing
inline flags must be on separate lines from the rest of the HTML body (for
now). There are some odd peculiarities, such as the need for one line buffers
between the inlne modules.
## TODO

- [ ] Implement POSTing for inline files
- [X] Implement HTTPS in practice (it is there in theory currently)
- [ ] Allow the uploading of files to the webserver
- [X] Allow more than just 'text/html' mimetypes
- [X] Do multithreading so that the entire server doesn't get held up if 
  there's one long request
- [ ] ~Migrate the entire webserver over to C~
