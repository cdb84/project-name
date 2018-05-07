#ifndef _HEATHEN_H
#define _HEATHEN_H
#include <string.h>
struct post_dict{
  char* index;
  char* value;
};
int sift_args( struct post_dict buffer[], int argc, char* args[] );
int indexof( struct post_dict haystack[], int haystackc, char* needle );
#endif
