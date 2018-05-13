#include <stdio.h>
#include <unistd.h>

int main(){
  puts(" it should always work.");
  for ( int i = 0; i < 100; i++){
    printf("%d \n", i);
  }
  sleep(60);
}

