import os,re,json,collections,sys
sys.path.insert(0,'.')
from leanstat import KW
R='curve25519-dalek-fork'; L=R+'/curve25519-dalek/lean'
BOILER={'import','module','open','namespace','section','end','variable','set_option','universe','attribute'}
DEFK={'def','abbrev','structure','inductive','class','instance','opaque','axiom','notation','macro','syntax','elab','irreducible_def'}
PROOFK={'theorem','lemma','example'}
def chunks(path):
    """yield (kind, [code lines]) per top-level item; comments/blank excluded"""
    kind='other'; buf=[]; inblock=0; out=[]
    for raw in open(path,errors='ignore'):
        s=raw.strip()
        if inblock:
            inblock=max(0,inblock+s.count('/-')-s.count('-/')); continue
        if s.startswith('/-'):
            inblock=max(0,s.count('/-')-s.count('-/')); continue
        if not s or s.startswith('--'): continue
        m=KW.match(s)
        if m and not raw[0].isspace():
            if buf: out.append((kind,buf))
            kind=m.group(1); buf=[]
        buf.append(raw.rstrip('\n'))
    if buf: out.append((kind,buf))
    return out
def files(p):
    if os.path.isfile(p): return [p]
    return [os.path.join(r,f) for r,ds,fs in os.walk(p) for f in fs if f.endswith('.lean')]
def tally(paths, proof_dir=False):
    c=collections.Counter()
    for p in paths:
        for f in files(p):
            for k,b in chunks(f):
                n=len(b)
                if k in BOILER: c['boiler']+=n
                elif k in PROOFK or proof_dir: c['proof']+=n
                elif k in DEFK: c['def']+=n
                elif k=='recall': c['spec']+=n
                elif k in ('#guard_msgs','#print','#check'): c['check']+=n
                else: c['other']+=n
    return c
res={}
# Rust
def rust(d):
    code=0
    for r,ds,fs in os.walk(d):
        ds[:]=[x for x in ds if x not in('tests','benches','examples')]
        for f in fs:
            if not f.endswith('.rs'): continue
            ib=False
            for line in open(os.path.join(r,f),errors='ignore'):
                s=line.strip()
                if ib:
                    if '*/' in s: ib=False
                    continue
                if not s or s.startswith('//'): continue
                if s.startswith('/*'):
                    if '*/' not in s: ib=True
                    continue
                code+=1
    return code
res['rust']=rust(R+'/curve25519-dalek/src')
res['translation']=sum(len(b) for f in [L+'/Curve25519Dalek/Funs.lean',L+'/Curve25519Dalek/Types.lean'] for k,b in chunks(f) if k not in BOILER)
res['specs']=tally([L+'/Specs'])
# trusted reading set (README): Defs, Curve25519 except Proofs, externals, Subtle Types/Contract, Zeroize Contract
c25=[os.path.join(R,'Curve25519',x) for x in os.listdir(R+'/Curve25519') if x!='Proofs']+[R+'/Curve25519.lean']
res['trusted']=tally([L+'/Defs',L+'/Curve25519Dalek/FunsExternal.lean',L+'/Curve25519Dalek/TypesExternal.lean',
    R+'/Subtle/Types.lean',R+'/Subtle/Contract.lean',R+'/Zeroize/Contract.lean']+c25)
res['proofdirs']=tally([L+'/Proofs',R+'/Curve25519/Proofs',R+'/Subtle/Lemmas.lean',R+'/Subtle/Instances.lean',
    R+'/Zeroize/Lemmas.lean',R+'/Zeroize/Instances.lean'], proof_dir=True)
res['ellipticcurve']=tally(['elliptic-curve/EllipticCurve'])
# distinct spec statements
blocks=[]
for f in files(L+'/Specs'):
    for k,b in chunks(f):
        if k=='recall': blocks.append(' '.join(x.strip() for x in b))
norm=lambda t: re.sub(r'«[^»]*»','«V»',re.sub(r'\b(52|26|51|2625|u64|u32)\b','N',t))
res['recall_blocks']=len(blocks); res['recall_distinct']=len(set(map(norm,blocks)))
dl=collections.defaultdict(int)
for f in files(L+'/Specs'):
    for k,b in chunks(f):
        if k=='recall': dl[norm(' '.join(x.strip() for x in b))]=len(b)
res['recall_distinct_lines']=sum(dl.values())
print(json.dumps(res,indent=1,default=dict))
json.dump(res,open('dalek-measure.json','w'),indent=1,default=dict)
