/* Two real GBA cores joined by mGBA's own GBA SIO lockstep driver (the code behind
 * mGBA-Qt's multiplayer window), stepped from one thread. The lockstep callbacks follow
 * MultiplayerController.cpp (0.10.5) exactly, with "thread waiting" replaced by an awake flag
 * that this loop honours between runLoop calls.
 *
 *   linkharness ROM0 SAV0 ROM1 SAV1     player 0 is the link master
 * stdin commands (one per line), each answered with one line:
 *   run N           advance until both cores ran N more frames      -> ok F0 F1 | stall F0 F1
 *   keys P MASK     hold GBA key mask on player P                   -> ok
 *   read P ADDR LEN bus read                                        -> hex
 *   shot P PATH     raw 240x160 XBGR8 frame                         -> ok
 *   quit            deinit cores (flushes the .sav files)           -> bye
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/gba/core.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/sio/lockstep.h>
#include <mgba-util/vfs.h>

#define N 2
static struct mCore* cores[N];
static color_t* video[N];
static struct GBASIOLockstep ls;
static struct GBASIOLockstepNode nodes[N];
static int awake[N] = {1, 1};
static int32_t posted[N];
static unsigned waitMask;

static void quiet(struct mLogger* l, int c, enum mLogLevel lv, const char* f, va_list a) {
	(void) l; (void) c; (void) lv; (void) f; (void) a;
}
static struct mLogger logger = { .log = quiet };

static bool cbSignal(struct mLockstep* l, unsigned mask) {
	(void) l;
	waitMask &= ~mask;
	if (!waitMask && awake[0] < 1) {
		awake[0] = 1;
		return true;
	}
	return false;
}
static bool cbWait(struct mLockstep* l, unsigned mask) {
	(void) l;
	waitMask |= mask;
	if (awake[0] > 0) {
		awake[0] = 0;
		return true;
	}
	return false;
}
static void cbAddCycles(struct mLockstep* l, int id, int32_t cycles) {
	(void) l;
	if (cycles < 0)
		abort();
	if (!id) {
		for (int i = 1; i < N; ++i) {
			if (nodes[i].d.p->mode > SIO_MULTI)
				continue;
			posted[i] += cycles;
			if (awake[i] < 1)
				nodes[i].nextEvent += posted[i];
			awake[i] = 1;
		}
	} else {
		posted[id] += cycles;
	}
}
static int32_t cbUseCycles(struct mLockstep* l, int id, int32_t cycles) {
	(void) l;
	posted[id] -= cycles;
	if (posted[id] <= 0)
		awake[id] = 0;
	return posted[id];
}
static int32_t cbUnusedCycles(struct mLockstep* l, int id) {
	(void) l;
	return posted[id];
}
static void cbUnload(struct mLockstep* l, int id) {
	(void) l;
	if (id) {
		posted[id] = 0;
		waitMask &= ~(1u << id);
		if (!waitMask && awake[0] < 1)
			awake[0] = 1;
	} else {
		for (int i = 1; i < N; ++i) {
			posted[i] += ls.players[0]->eventDiff;
			if (awake[i] < 1) {
				nodes[i].nextEvent += posted[i];
				awake[i] = 1;
			}
		}
	}
}

static struct mCore* boot(const char* rom, const char* sav, int i) {
	struct mCore* core = GBACoreCreate();
	if (!core || !core->init(core))
		return NULL;
	mCoreInitConfig(core, NULL);
	video[i] = calloc(256 * 256, sizeof(color_t));
	core->setVideoBuffer(core, video[i], 240);
	if (!mCoreLoadFile(core, rom))
		return NULL;
	struct VFile* vf = VFileOpen(sav, O_RDWR);
	if (!vf || !core->loadSave(core, vf))
		return NULL;
	core->reset(core);
	return core;
}

int main(int argc, char** argv) {
	if (argc != 1 + 2 * N) {
		fprintf(stderr, "usage: linkharness ROM0 SAV0 ROM1 SAV1\n");
		return 2;
	}
	mLogSetDefaultLogger(&logger);
	mLockstepInit(&ls.d);
	GBASIOLockstepInit(&ls);
	ls.d.signal = cbSignal;
	ls.d.wait = cbWait;
	ls.d.addCycles = cbAddCycles;
	ls.d.useCycles = cbUseCycles;
	ls.d.unusedCycles = cbUnusedCycles;
	ls.d.unload = cbUnload;
	for (int i = 0; i < N; ++i) {
		cores[i] = boot(argv[1 + 2 * i], argv[2 + 2 * i], i);
		if (!cores[i]) {
			fprintf(stderr, "failed to boot player %d\n", i);
			return 1;
		}
		struct GBA* gba = cores[i]->board;
		GBASIOLockstepNodeCreate(&nodes[i]);
		GBASIOLockstepAttachNode(&ls, &nodes[i]);
		GBASIOSetDriver(&gba->sio, &nodes[i].d, SIO_MULTI);
		GBASIOSetDriver(&gba->sio, &nodes[i].d, SIO_NORMAL_32);
	}
	setvbuf(stdout, NULL, _IOLBF, 0);
	char line[512];
	while (fgets(line, sizeof line, stdin)) {
		char cmd[16], path[400];
		int p;
		unsigned long a, b;
		if (sscanf(line, "run %lu", &a) == 1) {
			uint32_t start[N], target[N];
			for (int i = 0; i < N; ++i) {
				start[i] = cores[i]->frameCounter(cores[i]);
				target[i] = start[i] + a;
			}
			unsigned long budget = 4000000ul * (a + 1);
			for (;;) {
				int done = 1, pick = -1;
				uint32_t best = 0xFFFFFFFF;
				for (int i = 0; i < N; ++i) {
					uint32_t f = cores[i]->frameCounter(cores[i]);
					if (f < target[i])
						done = 0;
					if (awake[i] > 0 && f - start[i] < best) {
						best = f - start[i];
						pick = i;
					}
				}
				if (done || pick < 0 || !budget--)
					break;
				cores[pick]->runLoop(cores[pick]);
			}
			int ok = 1;
			for (int i = 0; i < N; ++i)
				ok &= cores[i]->frameCounter(cores[i]) >= target[i];
			printf("%s %u %u\n", ok ? "ok" : "stall", cores[0]->frameCounter(cores[0]), cores[1]->frameCounter(cores[1]));
		} else if (sscanf(line, "keys %d %lu", &p, &a) == 2 && p >= 0 && p < N) {
			cores[p]->setKeys(cores[p], (uint32_t) a);
			puts("ok");
		} else if (sscanf(line, "read %d %lx %lu", &p, &a, &b) == 3 && p >= 0 && p < N && b <= 65536) {
			for (unsigned long k = 0; k < b; ++k)
				printf("%02x", cores[p]->busRead8(cores[p], (uint32_t) (a + k)));
			putchar('\n');
		} else if (sscanf(line, "shot %d %399s", &p, path) == 2 && p >= 0 && p < N) {
			FILE* f = fopen(path, "wb");
			for (int y = 0; f && y < 160; ++y)
				fwrite(&video[p][y * 240], sizeof(color_t), 240, f);
			if (f)
				fclose(f);
			puts(f ? "ok" : "err");
		} else if (sscanf(line, "%15s", cmd) == 1 && !strcmp(cmd, "quit")) {
			break;
		} else {
			puts("err");
		}
	}
	for (int i = 0; i < N; ++i) {
		struct GBA* gba = cores[i]->board;
		GBASIOSetDriver(&gba->sio, NULL, SIO_MULTI);
		GBASIOSetDriver(&gba->sio, NULL, SIO_NORMAL_32);
		cores[i]->deinit(cores[i]);
	}
	puts("bye");
	return 0;
}
