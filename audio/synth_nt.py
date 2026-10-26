import numpy as np, scipy.signal as ss, scipy.io.wavfile as wf
SR=44100; DUR=27.00; N=int(SR*DUR)
L=np.zeros(N); R=np.zeros(N)
BPM=100; B=60/BPM
rng=np.random.default_rng(3)
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*SR); n=min(len(sig),N-i)
    if n<=0: return
    L[i:i+n]+=sig[:n]*g*(1-max(0,pan)); R[i:i+n]+=sig[:n]*g*(1+min(0,pan))
def hz(m): return 440*2**((m-69)/12)
def marimba(m,d=0.5):
    t=np.arange(int(SR*d))/SR; f=hz(m)
    s=np.sin(2*np.pi*f*t)*np.exp(-t*4)+0.5*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*9)+0.25*np.sin(2*np.pi*f*5.4*t)*np.exp(-t*16)
    a=np.minimum(1,t/0.002); return s*a
def bass(m,d):
    t=np.arange(int(SR*d))/SR; f=hz(m)
    s=ss.sawtooth(2*np.pi*f*t,0.5)*0.8+np.sin(2*np.pi*f*t)
    s*=np.exp(-t*3.5)*np.minimum(1,t/0.004)
    b,a=ss.butter(2,600/(SR/2)); return ss.lfilter(b,a,s)
def kick():
    t=np.arange(int(SR*.35))/SR; f=45+80*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
def noise(d,lo,hi,dec):
    t=np.arange(int(SR*d))/SR; n=rng.standard_normal(len(t))
    b,a=ss.butter(2,[lo/(SR/2),hi/(SR/2)],'band'); return ss.lfilter(b,a,n)*np.exp(-t*dec)
def clap():
    s=noise(.25,900,5000,18); env=np.ones_like(s)
    for k in (0,.012,.024): pass
    return s
def pad(ms,d):
    t=np.arange(int(SR*d))/SR; s=sum(ss.sawtooth(2*np.pi*hz(m)*t*(1+dt)) for m in ms for dt in (-0.004,0.004))
    b,a=ss.butter(2,1400/(SR/2)); s=ss.lfilter(b,a,s)
    env=np.minimum(1,t/0.3)*np.minimum(1,(d-t)/0.3); return s*env*0.05
CH=[(48,[60,64,67]),(43,[59,62,67]),(45,[60,64,69]),(41,[60,65,69])]  # C G Am F
MEL=[76,79,81,79,76,74,72,74, 74,79,74,71,74,76,74,0, 72,76,81,79,76,72,76,79, 77,76,74,72,69,72,74,0]
nbars=int(DUR/(4*B))+1
for bar in range(nbars):
    t0=bar*4*B; root,ch=CH[bar%4]
    add(pad(ch,4*B),t0,g=1.3)
    for b in range(4):
        tb=t0+b*B
        add(bass(root+(12 if b==3 else 0),B*0.9),tb,g=0.35)
        if bar>=2: add(kick(),tb,g=0.45)
        if b in (1,3) and bar>=2: add(clap(),tb,g=0.12,pan=0.1)
        add(noise(.05,7000,15000,80),tb+B/2,g=0.05,pan=-0.3)
    if bar>=1:
        for k in range(8):
            m=MEL[((bar-1)%4)*8+k]
            if m: add(marimba(m+12,1.0),t0+k*B/2,g=0.22,pan=0.2*((k%2)*2-1))
    else:
        for k,m in enumerate([72,76,79,84]): add(marimba(m,0.8),t0+k*B,g=0.3)
music=np.stack([L,R],1)
# effetti sonori
fx=np.zeros(N)
def addfx(sig,t,g):
    i=int(t*SR); n=min(len(sig),N-i); fx[i:i+n]+=sig[:n]*g
def whoosh(d):
    n=noise(d,300,6000,0); t=np.arange(len(n))/SR; return n*np.sin(np.pi*t/d)**2
def pop(f0=500):
    t=np.arange(int(SR*.12))/SR; f=f0*(1+3*np.exp(-t*60))
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*30)
def boing():
    t=np.arange(int(SR*.4))/SR; f=180+120*np.sin(2*np.pi*9*t)*np.exp(-t*6)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)
def chime(ms):
    return sum(marimba(m+12,1.2) for m in ms)
addfx(whoosh(1.6),5.10,0.3)
addfx(chime([84,88,91]),5.83,0.3)
addfx(chime([79,84]),6.70,0.2)
addfx(pop(500),8.23,0.35)
addfx(chime([88]),8.47,0.25)
addfx(chime([72,76,79,84]),10.17,0.3)
for i in range(14): addfx(chime([84+(i%5)*2]),14.37+i*2.5/30,0.09)
for k,a in enumerate([6,22,38]): addfx(chime([91+k*2]),14.10+a/30,0.14)
addfx(chime([72,79,84,88]),15.93,0.3)
addfx(whoosh(1.4),17.37,0.3)
for k in range(60): addfx(chime([86+int(rng.integers(0,12))]),18.37+k*0.045,0.05)
for i in range(3): addfx(pop(450+i*100),18.83+i*17/30,0.4)
addfx(whoosh(.6),21.37,0.25)
for i in range(3): addfx(pop(380),21.70+i*7/30,0.35)
mix=music*0.9+fx[:,None]
# fade out
fo=np.ones(N); i=int(SR*26.00); fo[i:]=np.linspace(1,0,N-i); mix*=fo[:,None]
mix/=np.max(np.abs(mix))*1.05
wf.write('/home/claude/reel-cucce/audio/nt_music.wav',SR,(mix*32767).astype(np.int16))
