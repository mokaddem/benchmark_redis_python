#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <hiredis/hiredis.h>

unsigned long getMicrotime(){
    struct timeval currentTime;
    gettimeofday(&currentTime, NULL);
    return currentTime.tv_sec * (int)1e6 + currentTime.tv_usec;
}

int main(int argc, char **argv) {
    redisContext *c;
    redisReply *reply;

    c = redisConnect("127.0.0.1", 6379);
    if (c == NULL || c->err) {
        if (c) {
            printf("Error: %s\n", c->errstr);
        } else {
            printf("Can't allocate redis context\n");
        }
    }
    //reply = redisCommand(c, "SET foo bar");
    int cd = 100;
    int d = 1000;
    int i, j;
    int cpush;
    int cpop;
    unsigned long tpush;
    unsigned long tpop;
    unsigned long tpushA[10];
    unsigned long tpopA[10];
    unsigned long t1;
    char *payload  = "LPUSH k AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

    for( int count=0; count<10; count+=1) {
        cpush = 0;
        cpop = 0;
        tpush = 0;
        tpop = 0;
        for( i = 0; i < cd; i = i + 1 ){
            t1 = getMicrotime();
            for( j = 0; j < d; j = j + 1 ) {
                reply = redisCommand(c, payload);
                freeReplyObject(reply);
                cpush += 1;
            }
            tpush += getMicrotime()-t1;
            t1 = getMicrotime();
            for( j = 0; j < d; j = j + 1 ) {
                reply = redisCommand(c, "RPOP k");
                freeReplyObject(reply);
                cpop += 1;
            }
            tpop += getMicrotime()-t1;
        }
        fprintf(stdout, "%lu\n", tpop);
        tpushA[count] = tpush;
        tpopA[count] = tpop;
    }

    redisFree(c);
    fprintf(stdout, "push\n");
    for (int i=0; i<10; i++) {
        fprintf(stdout, "%lu, ", (unsigned long) tpushA[i]);
    }
    fprintf(stdout, "\n# %d\n", cpush);

    fprintf(stdout, "pop\n");
    for (int i=0; i<10; i++) {
        fprintf(stdout, "%lu, ", (unsigned long) tpopA[i]);
    }
    fprintf(stdout, "\n# %d\n", cpop);

    return 0;
}
