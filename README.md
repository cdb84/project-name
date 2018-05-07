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

## TODO

- [ ] Implement HTTPS in practice (it is there in theory currently)
- [ ] Allow the uploading of files to the webserver
- [ ] Allow more than just 'text/html' mimetypes
- [ ] Do multithreading so that the entire server doesn't get held up if there's
      one long request
