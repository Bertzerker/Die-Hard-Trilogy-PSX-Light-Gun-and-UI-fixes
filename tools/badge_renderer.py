"""Reversible DH2 HUD aspect test in DuckStation RAM; never writes the CD image.

Reimplements the original SPRT helper inside its existing code footprint. Only
the health-strip caller gets an FT4 with a 32x19 destination and full UV range.
Other callers retain their 32x32 SPRT, palette, blending, and ordering behavior.
"""
import struct

BASE, END = 0x80046C30, 0x80046E68
R = {n:i for i,n in enumerate('zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split())}

def build(height=19):
    words, labels, branches = [], {}, []
    def emit(w): words.append(w)
    def imm(op,t,s,k): emit((op<<26)|(R[s]<<21)|(R[t]<<16)|(k&65535))
    def rr(fn,d,s,t='zero'): emit((R[s]<<21)|(R[t]<<16)|(R[d]<<11)|fn)
    def shift(d,t,n,fn=0): emit((R[t]<<16)|(R[d]<<11)|(n<<6)|fn)
    def li(t,k): imm(13,t,'zero',k)
    def lui(t,k): imm(15,t,'zero',k)
    def add(t,s,k): imm(9,t,s,k)
    def lw(t,k,s): imm(35,t,s,k)
    def lh(t,k,s): imm(33,t,s,k)
    def lhu(t,k,s): imm(37,t,s,k)
    def lbu(t,k,s): imm(36,t,s,k)
    def sw(t,k,s): imm(43,t,s,k)
    def sh(t,k,s): imm(41,t,s,k)
    def sb(t,k,s): imm(40,t,s,k)
    def move(d,s): rr(33,d,s)
    def nop(): emit(0)
    def branch(op,s,t,label):
        branches.append((len(words),label)); imm(op,t,s,0)
    def jump(label): branch(4,'zero','zero',label)
    def call(a): emit(0x0C000000|((a>>2)&0x3FFFFFF))
    def label(n): labels[n]=len(words)

    add('sp','sp',-40)
    for reg,off in [('ra',36),('s0',32),('s1',28),('s2',24),('s3',20)]: sw(reg,off,'sp')
    lui('s3',0x800B); lw('s0',0x7140,'s3'); lw('t0',0x70A8,'s3')
    li('t1',0xD7F3); rr(35,'t0','s0','t0'); rr(42,'t0','t1','t0')
    branch(5,'t0','zero','done'); shift('s2','a2',2)
    # Texture record, indexed by signed 16-bit sprite number.
    shift('a1','a1',16); shift('a1','a1',16,3)
    shift('t0','a1',4); rr(35,'t0','t0','a1'); shift('t0','t0',2)
    lui('s1',0x8016); add('s1','s1',-5256); rr(33,'s1','s1','t0')
    lh('t0',0,'a0'); lh('t1',2,'a0'); add('t0','t0',-16)
    sh('t0',8,'s0'); add('t1','t1',-16); sh('t1',10,'s0')
    li('t2',32); sh('t2',16,'s0'); sh('t2',18,'s0')
    lhu('t2',0,'s1'); lhu('t3',2,'s1'); sh('t2',12,'s0')
    lhu('t4',6,'s1'); li('t5',0x64)
    shift('a3','a3',16); shift('a3','a3',16,3)
    # Negative intensity: alternate palette/tpage and semitransparency.
    imm(10,'t6','a3',0); branch(4,'t6','zero','nonnegative'); nop()
    lhu('t3',40,'s1'); lhu('t4',34,'s1'); li('t5',0x66)
    jump('color'); rr(35,'a3','zero','a3')
    label('nonnegative'); li('t6',255)
    branch(5,'a3','t6','color'); nop()
    lhu('t3',40,'s1'); li('t5',0x65)
    label('color'); sh('t3',14,'s0'); sb('a3',4,'s0'); sb('a3',5,'s0'); sb('a3',6,'s0')
    sb('t5',7,'s0'); li('t6',4); sb('t6',3,'s0')
    # Only the bottom-left badge-strip call gets aspect correction.
    lui('t6',0x8005); add('t6','t6',-17832)  # 0x8004BA58
    branch(5,'ra','t6','sprite'); li('t7',20)
    add('t5','t5',-0x38); sb('t5',7,'s0'); li('t6',9); sb('t6',3,'s0')
    # Keep the original bottom edge. The artwork is resampled, not cropped.
    add('t1','t1',32-height); sh('t1',10,'s0')
    add('t6','t0',32); sh('t6',16,'s0'); sh('t1',18,'s0')
    add('t1','t1',height); sh('t0',24,'s0'); sh('t1',26,'s0')
    sh('t6',32,'s0'); sh('t1',34,'s0')
    # Inclusive UV endpoints keep tiles ending at 255 on their own atlas tile.
    lbu('t0',0,'s1'); lbu('t1',1,'s1'); add('t6','t0',31)
    sb('t6',20,'s0'); sb('t1',21,'s0'); sh('t4',22,'s0')
    add('t1','t1',31); sb('t0',28,'s0'); sb('t1',29,'s0')
    sb('t6',36,'s0'); sb('t1',37,'s0'); li('t7',40)
    label('sprite'); move('s1','t4'); sw('t7',16,'sp')
    lw('a0',0x7018,'s3'); move('a1','s0'); call(0x80083DA4); rr(33,'a0','a0','s2')
    lw('t7',16,'sp'); move('a3','s1'); rr(33,'s0','s0','t7')
    sw('zero',16,'sp'); move('a0','s0'); li('a1',1); call(0x800820B4); li('a2',1)
    lw('a0',0x7018,'s3'); move('a1','s0'); call(0x80083DA4); rr(33,'a0','a0','s2')
    add('s0','s0',12); sw('s0',0x7140,'s3')
    label('done')
    for reg,off in [('ra',36),('s0',32),('s1',28),('s2',24),('s3',20)]: lw(reg,off,'sp')
    emit(0x03E00008); add('sp','sp',40)
    for i,n in branches: words[i] |= (labels[n]-i-1)&65535
    result=struct.pack('<%dI'%len(words),*words)
    assert len(result)<=END-BASE, (len(result),END-BASE)
    return result + bytes(END-BASE-len(result))

