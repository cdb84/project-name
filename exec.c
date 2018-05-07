#include <stdio.h>
#include <string.h>
#include "heathen.h"
/*
 * DATA SECTION
 */
char* HEAD =
  "<head>"
  "<title>This Website Shouldn't Exist</title>"
  "</head>\n";
static void put_header( ){
  printf( "%s", HEAD );
}
int main( int argc, char* args[] ){
  int pargc = ( argc-1 )/2;
  struct post_dict post_args[pargc];
  sift_args( post_args, argc, args );
  int indexof_lastname = indexof( post_args, pargc, "lastname" );
  int indexof_lang = indexof( post_args, pargc, "language" );
  put_header( );
  printf( "<h1>Hello Mr(s). %s </h1>\n", post_args[ indexof_lastname ].value );
  if ( !strcmp( post_args[ indexof_lang ].value, "php" ) ){
    printf( "<p>Why are you like this. Why. PHP may have cleaned up in recent"
	    " years, but think about the benefits of other backends, such as"
	    " the platform I have just for: C! You could use any language"
	    " you really want for this back end actually.</p>\n" );
  }
  else if ( !strcmp( post_args[ indexof_lang ].value, "c" ) ){
    printf( "<p>I see you put your money where your mouth is.</p>" );
  }
  else if ( !strcmp( post_args[ indexof_lang ].value, "lisp" ) ){
    printf( "<p>The 70s called, you dropped a parenthesis.</p>" );
  }
}
