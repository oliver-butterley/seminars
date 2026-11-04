import os,re,sys,collections
KW=re.compile(r'^(?:@\[[^\]]*\]\s*)?(?:(?:private|protected|noncomputable|public|partial|unsafe|nonrec|scoped|local)\s+)*(theorem|lemma|def|abbrev|structure|inductive|class|instance|opaque|axiom|recall|example|notation|macro|syntax|elab|attribute|#guard_msgs|#print|#check|open|namespace|section|end|variable|set_option|import|module|universe|irreducible_def)\b')
def classify(path):
    """return Counter of kind -> code lines (non-blank, non-comment)"""
    c=collections.Counter(); kind='other'; inblock=0
    for raw in open(path,errors='ignore'):
        s=raw.strip()
        # block comments incl docstrings, nested
        if inblock:
            inblock+=s.count('/-')-s.count('-/')
            continue
        if s.startswith('/-'):
            inblock=s.count('/-')-s.count('-/')
            if inblock<0: inblock=0
            continue
        if not s or s.startswith('--'): continue
        m=KW.match(s)
        if m and not raw[0].isspace():
            kind=m.group(1)
        c[kind]+=1
    return c
def walk(paths):
    tot=collections.Counter()
    for p in paths:
        if os.path.isfile(p): tot+=classify(p); continue
        for r,ds,fs in os.walk(p):
            for f in fs:
                if f.endswith('.lean'): tot+=classify(os.path.join(r,f))
    return tot
if __name__=='__main__':
    for p in sys.argv[1:]:
        c=walk([p]); print(f"{p}: total {sum(c.values())}  "+", ".join(f"{k}:{v}" for k,v in c.most_common(8)))
