from pathlib import Path
import struct,json
ROOT=Path(__file__).parent
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
class Disc:
 def __init__(self,p): self.p=p; self.f=p.open('rb')
 def data(self,lba,n):
  out=bytearray()
  for s in range(lba,lba+(n+2047)//2048):
   self.f.seek(s*2352+24);out.extend(self.f.read(2048))
  return bytes(out[:n])
 def files(self):
  pvd=self.data(16,2048);assert pvd[1:6]==b'CD001'
  r=pvd[156:190]; result=[]
  def walk(lba,size,prefix):
   b=self.data(lba,size);o=0
   while o<len(b):
    n=b[o]
    if not n:o=(o//2048+1)*2048;continue
    r=b[o:o+n];o+=n;name=r[33:33+r[32]]
    if name in (b'\x00',b'\x01'):continue
    name=prefix+name.decode('ascii');loc=u32(r,2);sz=u32(r,10)
    if r[25]&2:walk(loc,sz,name+'/')
    else:result.append((name,loc,sz))
  walk(u32(r,2),u32(r,10),'');return result
