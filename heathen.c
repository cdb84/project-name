#include <string.h>
struct post_dict{
  char* index;
  char* value;
};
/*
 * sift_args takes the normal array of args and sifts them into a dictionary
 * based on form of 'index':'value'
 * post_dict buffer = receiving buffer
 * argc = the argument count brought into the program originally
 * args[] = the arguments originally passed to the program
 * On error, returns nonzero value. The optional arguments (separate from the
 * program identifier) must be evenly divisible by two.
 */
int sift_args( struct post_dict buffer[], int argc, char* args[] ){
  int post_argc = argc-1;
  if ( post_argc % 2 == 0 ){
    for ( int i = 1, j = 0; i < argc; i+=2, j++ ){
      struct post_dict item = { args[i], args[i+1] };
      buffer[j] = item;
    }
    return 0;
  }
  return 1;
}
/*
 * Returns index in post_dict haystack of 'needle' identifier 
 */
int indexof( struct post_dict haystack[], int haystackc, char* needle ){
  for ( int i = 0; i < haystackc; i++ ){
    if ( !strcmp( haystack[i].index, needle ) ){
      return i;
    }
  }
  return -1; 
}
