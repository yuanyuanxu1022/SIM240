import os, re, time, gc, datetime
os.environ["OMP_NUM_THREADS"]="1"; os.environ["MKL_NUM_THREADS"]="1"
import av, numpy as np
path = "/home/dell/yuanyuanxu/SIM240/docs/reports/meeting_20261112/会议录音_20261112_1427.m4a"
outfile = "/home/dell/yuanyuanxu/SIM240/docs/reports/meeting_20261112/转写全文_逐段.md"
# 断点：读已有文件的最后时间戳
last_t = -1
if os.path.exists(outfile):
    for line in open(outfile):
        m = re.match(r"\[(\d+):(\d+)\]", line)
        if m: last_t = int(m.group(1))*60 + int(m.group(2))
print("resume from second:", last_t+1, flush=True)
c = av.open(path)
resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
chunks = []
for frame in c.decode(audio=0):
    for rf in resampler.resample(frame):
        chunks.append(rf.to_ndarray().flatten().astype(np.float32) / 32768.0)
audio = np.concatenate(chunks)
del chunks; gc.collect()
total = len(audio)//16000
print("decoded seconds:", total, flush=True)
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=1)
SR = 16000; STEP = 120 * SR; OV = 2 * SR
mode = "a" if last_t >= 0 and os.path.getsize(outfile) else "w"
out = open(outfile, mode)
if mode == "w":
    out.write("# 会议录音转写（2026-11-12 14:27，时长约 48 分钟）\n\n逐段时间戳为录音内相对时间。\n\n")
pos = max(0, ((last_t+1) // 120) * 120 * SR)
while pos < len(audio):
    seg = audio[pos: pos + STEP + OV]
    t0 = pos / SR
    ok = False
    for attempt in range(4):
        try:
            segs, _ = model.transcribe(seg, language="zh", vad_filter=True, beam_size=3)
            for s in segs:
                st = int(t0 + s.start)
                if st <= last_t and mode == "a": continue
                t = datetime.timedelta(seconds=st)
                out.write(f"[{str(t)[-6:]}] {s.text.strip()}\n"); out.flush()
            ok = True; break
        except Exception as e:
            print(f"chunk@{t0:.0f}s attempt{attempt+1} failed: {type(e).__name__}", flush=True)
            gc.collect(); time.sleep(10)
    if not ok:
        print("GIVEUP at", t0, flush=True); break
    pos += STEP
    del seg; gc.collect()
out.close()
print("DONE" if pos >= len(audio) else "INCOMPLETE", flush=True)
