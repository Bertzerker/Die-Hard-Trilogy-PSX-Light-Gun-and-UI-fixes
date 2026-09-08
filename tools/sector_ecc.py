"""Apply the supplied Nuvee flash-removal notes, with backups and sector verification."""
import struct
import hashlib
F=[0]*256;B=[0]*256;E=[]
for i in range(256):
 j=i<<1
 if j&256:j^=0x11d
 F[i]=j;B[i^j]=i
 x=i
 for _ in range(8):x=(x>>1)^(0xd8018001 if x&1 else 0)
 E.append(x)
def ecc(src,major,minor,mult,inc):
 out=bytearray(major*2);size=major*minor
 for m in range(major):
  idx=(m>>1)*mult+(m&1);a=b=0
  for _ in range(minor):
   v=src[idx];idx=(idx+inc)%size;a^=v;b^=v;a=F[a]
  a=B[F[a]^b];out[m]=a;out[m+major]=a^b
 return out
def repair(raw):
 s=bytearray(raw);assert s[15]==2 and not s[18]&32 and s[16:20]==s[20:24]
 edc=0
 for v in s[16:2072]:edc=(edc>>8)^E[(edc^v)&255]
 struct.pack_into('<I',s,2072,edc)
 hdr=s[12:16];s[12:16]=bytes(4)
 s[2076:2248]=ecc(s[12:2076],86,24,2,86)
 s[2248:2352]=ecc(s[12:2248],52,43,86,88)
 s[12:16]=hdr;return bytes(s)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
