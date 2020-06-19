// Header for utils.cpp, a little library of low-level array and timer stuff.
// (rest of finufft defs and types are now in defs.h)

#ifndef UTILS_H
#define UTILS_H

#include "dataTypes.h"

// ahb's low-level array helpers
FLT relerrtwonorm(BIGINT n, CPX* a, CPX* b);
FLT errtwonorm(BIGINT n, CPX* a, CPX* b);
FLT twonorm(BIGINT n, CPX* a);
FLT infnorm(BIGINT n, CPX* a);
void arrayrange(BIGINT n, FLT* a, FLT *lo, FLT *hi);
void indexedarrayrange(BIGINT n, BIGINT* i, FLT* a, FLT *lo, FLT *hi);
void arraywidcen(BIGINT n, FLT* a, FLT *w, FLT *c);
BIGINT next235even(BIGINT n);

// jfm's timer class
#include <sys/time.h>
class CNTime {
 public:
  void start();
  double restart();
  double elapsedsec();
 private:
  struct timeval initial;
};

// openmp helpers
int get_num_threads_parallel_block();

// thread-safe rand number generator for Windows platform
#ifdef _WIN32
#include <random>
int rand_r(unsigned int *seedp);
#endif

#endif  // UTILS_H
