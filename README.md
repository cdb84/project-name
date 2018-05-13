# heathen-webserver
A webserver I shouldn't have made but still did. On the plus side,
you can do webpage preprocessing in C now.
## This Is Terrifying
I know everyone hates on PHP, but I miss it ever so slighty now having
preprocessed in C. Anyway, this repository is more "should vs. could" than
anything, as in yes, we *could* do something so dastardly, but we really
shouldn'tve.

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
`python heathen.py [port] [-ssl]`

Note that SSL functionality is not yet confirmed to work properly (or even 
safely.)

### Browser
Simply navigate to the webserver's address, and enter the URL of an executable. 
That's all!

### Example files
In the master branch, there exists a few files:

- exec.c and exec.out, which can be called to as an individual executable that
the server can run as a pre-process
- index.html, the index of this webroot. Nothing really special here.
- test.hea, an inline 'heathen' file that you can *write C code in to
have preprocessed*:
```
<html>
<head>
</head>
<p>This is normal html, and sent to the client as such. However, you can do
$$'gcc INPUT.c /home/connor/git/lawless-webserver/libheathen.c -o OUTPUT'>
#include <stdio.h>

int main(){
  puts("The following!");
}
$$>
and it works inline!!!</p>
</html>
```
INPUT should specify where in your compiler statement the input file-path
goes, and OUTPUT should specify the output argument positioning.
This is done so that when the webserver live-compiles, it knows what
files and paths to send into the compile statement. The opening and closing
inline flags must be on separate lines from the rest of the HTML body (for
now).
## TODO

- [ ] Implement HTTPS in practice (it is there in theory currently)
- [ ] Allow the uploading of files to the webserver
- [ ] Allow more than just 'text/html' mimetypes
- [ ] Do multithreading so that the entire server doesn't get held up if there's
      one long request
- [ ] Migrate the entire webserver over to C
