import soundfile as sf, json
from kokoro_onnx import Kokoro
k=Kokoro("kokoro-v1.0.onnx","voices-v1.0.bin")
L=["Questa è l'Italia, di notte. E non c'è nemmeno un cane.",
"Ogni commento accende una luce: la cuccia del tuo cane, col suo nome.",
"Il primo cane di ogni città, diventa Fondatore. Per sempre.",
"Più punti fai, più la tua cuccia brilla.",
"Quale città si accenderà per prima? Milano? Roma? Napoli?",
"Scrivi la tua città, il nome, e la razza del tuo cane!"]
fps=30;t=0.7;S=[];D=[]
for i,l in enumerate(L):
    s,sr=k.create(l,voice="im_nicola",speed=1.06,lang="it"); sf.write(f"nt_{i}.wav",s,sr)
    seg=len(s)/sr+(0.6 if i<len(L)-1 else 2.4); S.append(round(t*fps)); D.append(round(seg*fps)); t+=seg
json.dump({"starts":S,"durs":D,"total":round(t*fps),"lines":L},open('/home/claude/reel-cucce/src/nt_timing.json','w'),ensure_ascii=False)
print(S,D,round(t,1))
