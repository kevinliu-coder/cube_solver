/* Lightweight k-center: sample 2000 states, radius 6, estimate centers needed */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define NP 40320
#define NT 2187
#define N_MOVES 18
#define MAX_RADIUS 6
#define N_SAMPLES 2000
#define Q_CAP (1 << 19) /* 512K entries */

uint16_t cpm[NP][N_MOVES];
uint16_t twm[NT][N_MOVES];
uint8_t *visited = NULL;

static inline int idx(int cp, int tw) { return cp * NT + tw; }
static inline void setv(int i) { visited[i>>3] |= (1<<(i&7)); }
static inline int isv(int i) { return visited[i>>3] & (1<<(i&7)); }

typedef struct { int cp, tw; uint8_t d; } QE;
QE *q; int qh, qt;
static inline void push(int cp, int tw, int d) {
    q[qt].cp=cp; q[qt].tw=tw; q[qt].d=d; qt=(qt+1)&(Q_CAP-1);
}
static inline QE pop(void) { QE e=q[qh]; qh=(qh+1)&(Q_CAP-1); return e; }

int bfs_cover(int cp0, int tw0, uint8_t *covered, int radius) {
    int bs = (NP*NT+7)/8;
    memset(visited, 0, bs);
    qh=qt=0; setv(idx(cp0,tw0)); push(cp0,tw0,0);
    int nc=0;
    while (qh!=qt) {
        QE e=pop();
        if (e.d >= radius) continue;
        for (int mi=0; mi<N_MOVES; mi++) {
            int ncp=cpm[e.cp][mi], ntw=twm[e.tw][mi];
            int ni=idx(ncp,ntw);
            if (!isv(ni)) {
                setv(ni); push(ncp,ntw,e.d+1);
                if (covered[ni>>3] & (1<<(ni&7))) {
                    covered[ni>>3] &= ~(1<<(ni&7)); nc++;
                }
            }
        }
    }
    return nc;
}

int main(void) {
    FILE *f=fopen("cpm.bin","rb");
    for(int p=0;p<NP;p++) fread(cpm[p],2,N_MOVES,f); fclose(f);
    f=fopen("twm.bin","rb");
    for(int t=0;t<NT;t++) fread(twm[t],2,N_MOVES,f); fclose(f);
    
    int bs=(NP*NT+7)/8;
    visited=(uint8_t*)calloc(1,bs);
    q=(QE*)malloc(Q_CAP*sizeof(QE));
    uint8_t *covered=(uint8_t*)calloc(1,bs);
    
    printf("Radius=%d, %d samples, memory=%dMB\n", MAX_RADIUS, N_SAMPLES, (bs*3+Q_CAP*sizeof(QE))>>20);
    
    /* Generate samples */
    int *scp=malloc(N_SAMPLES*4), *stw=malloc(N_SAMPLES*4);
    srand(42);
    int total_uncov=0;
    for(int i=0;i<N_SAMPLES;i++){
        int cp=0,tw=0;
        for(int s=5+rand()%20;s>0;s--){int mi=rand()%N_MOVES;cp=cpm[cp][mi];tw=twm[tw][mi];}
        scp[i]=cp; stw[i]=tw;
        int ii=idx(cp,tw);
        if(!(covered[ii>>3]&(1<<(ii&7)))){covered[ii>>3]|=(1<<(ii&7));total_uncov++;}
    }
    printf("%d unique samples\n",total_uncov);
    
    /* Greedy */
    int centers=0;
    time_t t0=time(NULL);
    while(total_uncov>0 && centers<200){
        int best=-1,bcov=-1;
        for(int ci=0;ci<N_SAMPLES && total_uncov>0;ci++){
            int ii=idx(scp[ci],stw[ci]);
            if(!(covered[ii>>3]&(1<<(ii&7)))) continue; /* already covered */
            if(rand()%100>3) continue; /* sample candidates for speed */
            uint8_t *tmp=malloc(bs); memcpy(tmp,covered,bs);
            int cv=bfs_cover(scp[ci],stw[ci],tmp,MAX_RADIUS);
            free(tmp);
            if(cv>bcov){bcov=cv;best=ci;}
        }
        if(best<0||bcov<=0) break;
        int nc=bfs_cover(scp[best],stw[best],covered,MAX_RADIUS);
        total_uncov-=nc; centers++;
        if(centers<=5||centers%20==0)
            printf("  C#%d: +%d covered, %d remain (%.0fs)\n",centers,nc,total_uncov,(double)(time(NULL)-t0));
    }
    
    printf("\n=== Results ===\n");
    printf("Radius=%d: %d centers cover %d/%d samples\n",
           MAX_RADIUS, centers, N_SAMPLES-total_uncov, N_SAMPLES);
    
    /* Extrapolate: if R radii cover X samples, full space needs C * (44M/samples) */
    double ratio = (double)N_SAMPLES / 44089920.0;
    int extrapolated = (int)(centers / ratio);
    printf("Extrapolated to full space (44M): ~%d centers\n", extrapolated);
    
    /* What if radius were 9? Each center at radius 9 covers ~(18^9/18^6)^(1/3) more */
    double grow = 18.0; /* approximate: each extra step multiplies by ~18 */
    double r9_factor = 1.0;
    for(int r=MAX_RADIUS+1; r<=9; r++) r9_factor *= (grow * 0.7); /* damped */
    printf("Estimate at radius 9: ~%.0f centers\n", extrapolated / r9_factor);
    printf("DP model predicted: 200 centers\n");
    
    free(visited);free(q);free(covered);free(scp);free(stw);
    return 0;
}
