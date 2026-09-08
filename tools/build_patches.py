"""Build independent PPF3 patches against the user's existing Nuvee GunCon BIN.

PPF3 layout follows the original MakePPF3 writer:
https://github.com/Sappharad/MultiPatch/blob/master/ppfdev/makeppf3_linux.c
Includes block check, undo records, and regenerated Mode2/Form1 EDC/ECC.
The source BIN is opened read-only throughout.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from disc_image import Disc,u32
ROOT=Path(__file__).resolve().parent.parent
from sector_ecc import repair,sha
from badge_renderer import build as badge_code,BASE,END
from hud_layout import VALUES

OUT=ROOT/'build'

def encode(desc,check,sectors):
    result=bytearray(b'PPF30\x02'+desc.encode('ascii').ljust(50,b' ')+bytes([0,1,1,0])+check)
    assert len(result)==1084
    records=0
    for sector,(old,new) in sorted(sectors.items()):
        i=0
        while i<2352:
            if old[i]==new[i]:i+=1;continue
            start=i
            while i<2352 and old[i]!=new[i] and i-start<255:i+=1
            result+=struct.pack('<QB',sector*2352+start,i-start)+new[start:i]+old[start:i]
            records+=1
    return bytes(result),records

def parse(path):
    data=path.read_bytes()
    assert data[:6]==b'PPF30\x02' and data[56:60]==bytes([0,1,1,0])
    cursor=1084; records=[]
    while cursor<len(data):
        offset,length=struct.unpack_from('<QB',data,cursor);cursor+=9
        assert length and cursor+2*length<=len(data)
        after=data[cursor:cursor+length];before=data[cursor+length:cursor+2*length]
        records.append((offset,before,after));cursor+=2*length
    assert cursor==len(data)
    return data[60:1084],records

def apply_records(sectors,records,undo=False):
    for offset,before,after in records:
        sector,within=divmod(offset,2352)
        assert within+len(after)<=2352
        if undo:before,after=after,before
        assert bytes(sectors[sector][within:within+len(before)])==before
        sectors[sector][within:within+len(after)]=after

def main():
    ap=argparse.ArgumentParser(description='Build PPFs from the supported Nuvee GunCon-patched Track 01 BIN.')
    ap.add_argument('source',type=Path)
    args=ap.parse_args()
    source=args.source.resolve()
    OUT.mkdir(exist_ok=True)
    source_hash=sha(source)
    assert source_hash=="1a2f348289285ad95cbaed49ffb535cc0d3792307a9a7d6c66fa6c486cdef3a1", "Unsupported base image; see README"
    disc=Disc(source)
    try:
        _,lba,size=next(x for x in disc.files() if x[0]=='DH2.EXE;1')
        exe=disc.data(lba,size);load=u32(exe,24)
        def old(addr,n):return exe[addr-load+2048:addr-load+2048+n]
        assert old(0x80088E94,4)==bytes.fromhex('0001a520')
        assert old(0x80088E9C,4)==bytes.fromhex('edffe720')
        ui=[(BASE,badge_code())]
        for addr,value in VALUES.items():
            assert u32(old(addr,4),0)>>26==13
            ui.append((addr,struct.pack('<H',value)+old(addr,4)[2:]))
        for addr in (0x8004C768,0x8004C784):
            assert old(addr,4)==struct.pack('<I',0x0C011B0C)
            ui.append((addr,bytes(4)))
        plans={
            'Gun Patch Mister':[(0x80088E94,bytes.fromhex('f300a520')),(0x80088E9C,bytes.fromhex('f3ffe720'))],
            'Gun Patch Emulator':[(0x80088E94,bytes.fromhex('f300a520')),(0x80088E9C,bytes.fromhex('e7ffe720'))],
            'Die Hard 2 UI Patch':ui,
        }
        disc.f.seek(0x9320);check=disc.f.read(1024)
        all_original={};outputs={};report=[]
        for name,edits in plans.items():
            sectors={}
            for addr,new in edits:
                for i,value in enumerate(new):
                    fileoff=addr-load+2048+i;sector=lba+fileoff//2048;within=24+fileoff%2048
                    if sector not in sectors:
                        disc.f.seek(sector*2352);original=disc.f.read(2352)
                        sectors[sector]=(original,bytearray(original));all_original[sector]=original
                    sectors[sector][1][within]=value
            validity={str(s):repair(a)==a for s,(a,b) in sectors.items()}
            sectors={s:(a,repair(b)) for s,(a,b) in sectors.items()}
            payload,count=encode('DH2 USA v1.1 GunCon: '+name,check,sectors)
            path=OUT/(name+'.ppf');path.write_bytes(payload)
            block,records=parse(path);assert block==check
            applied={s:bytearray(a) for s,(a,b) in sectors.items()}
            apply_records(applied,records)
            for s,(a,b) in sectors.items():assert bytes(applied[s])==b and repair(applied[s])==bytes(applied[s])
            # Validate executable bytes independently of sector checksum content.
            for addr,new in edits:
                actual=bytearray()
                for i in range(len(new)):
                    off=addr-load+2048+i;actual.append(applied[lba+off//2048][24+off%2048])
                assert actual==new
            apply_records(applied,list(reversed(records)),True)
            assert all(bytes(applied[s])==a for s,(a,b) in sectors.items())
            outputs[name]=(sectors,records)
            report.append({'file':path.name,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),
                'records':count,'sectors':sorted(sectors),'original_sector_checksums_valid':validity,
                'edits':[{'ram':hex(addr),'original':old(addr,len(new)).hex(),'patched':new.hex()} for addr,new in edits],
                'verification':'Parsed generated PPF, applied every record, verified executable edits and EDC/ECC, then undid to exact original sectors.'})
        combinations=[]
        for gun in ('Gun Patch Mister','Gun Patch Emulator'):
            gs,gr=outputs[gun];us,ur=outputs['Die Hard 2 UI Patch']
            assert not(set(gs)&set(us)), 'Independent patches must not share checksum sectors'
            for order in ((gr,ur),(ur,gr)):
                state={s:bytearray(a) for s,a in all_original.items()}
                for records in order:apply_records(state,records)
                assert all(bytes(state[s])==pair[1] for table in (gs,us) for s,pair in table.items())
                for records in reversed(order):apply_records(state,list(reversed(records)),True)
                assert all(bytes(state[s])==a for s,a in all_original.items())
            combinations.append(gun+' + UI: both application orders and reverse-order undo verified')
    finally:disc.f.close()
    assert sha(source)==source_hash, 'Source changed during build'
    manifest={'source':source.name,'source_bytes':source.stat().st_size,'source_sha256':source_hash,
        'required_baseline':'USA v1.1 SLUS-00119 with existing Nuvee USA Greatest Hits GunCon conversion',
        'source_unchanged':True,'patches':report,'combinations':combinations,
        'mister_status':'Candidate based on latest user illustration: X -13, Y +6; not hardware-tested',
        'emulator_status':'X -13, Y -6; user-tested in DuckStation',
        'format_source':'https://github.com/Sappharad/MultiPatch/blob/master/ppfdev/makeppf3_linux.c'}
    (OUT/'Verification.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:manifest[k] for k in ('source_sha256','source_unchanged','combinations')},indent=2))
    print('\n'.join(f'{x["file"]}: {x["bytes"]} bytes, {len(x["sectors"])} sectors' for x in report))

if __name__=='__main__':main()
