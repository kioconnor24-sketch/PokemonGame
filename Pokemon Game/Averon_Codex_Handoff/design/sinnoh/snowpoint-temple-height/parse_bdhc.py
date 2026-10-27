#!/usr/bin/env python3
"""Strict read-only BDHC geometry; rational planes are not DS runtime acceptance."""
from bisect import bisect_right
from fractions import Fraction
import struct

FX = 4096
TILE = 16 * FX


def decode(raw):
    if len(raw) < 16 or raw[:4] != b'BDHC':
        raise ValueError('missing or truncated BDHC header')
    counts = struct.unpack_from('<6H', raw, 4)
    formats = ('<ii', '<iii', '<i', '<4H', '<iHH', '<H')
    sizes = tuple(struct.calcsize(f) for f in formats)
    if any(n == 0 for n in counts):
        raise ValueError('empty BDHC table unsupported')
    if 16 + sum(n*s for n,s in zip(counts,sizes)) != len(raw):
        raise ValueError('BDHC table lengths/trailing bytes differ')
    arrays=[];offset=16
    for count,fmt,size in zip(counts,formats,sizes):
        arrays.append(tuple(struct.unpack_from(fmt,raw,offset+i*size) for i in range(count)))
        offset += count*size
    points,normals,constants,plates,strips,access=arrays
    constants=tuple(v[0] for v in constants);access=tuple(v[0] for v in access)
    for first,second,normal,constant in plates:
        if first>=len(points) or second>=len(points) or normal>=len(normals) or constant>=len(constants):
            raise ValueError('plate index outside table')
        if normals[normal][1] == 0:
            raise ValueError('vertical plane cannot determine height')
    if any(a[0]>=b[0] for a,b in zip(strips,strips[1:])):
        raise ValueError('strip scanlines must be strictly ascending')
    for _,count,start in strips:
        if not count or start+count>len(access):
            raise ValueError('strip access slice outside table')
        if len(set(access[start:start+count])) != count:
            raise ValueError('duplicate plate in strip access')
    if any(i>=len(plates) for i in access):
        raise ValueError('access plate index outside table')
    return dict(points=points,normals=normals,constants=constants,plates=plates,strips=strips,access=access)


def candidates(data,x,z):
    """Source inclusive bounds and strip routing, exact rational plane heights.

    Inputs use DS fx32 units. No nearest-height selection, fixed-point rounding,
    actor movement or dynamic terrain is claimed here. More than ten overlaps
    is refused rather than silently dropping candidates as the runtime does.
    """
    strips=data['strips']
    index=min(bisect_right([v[0] for v in strips],z),len(strips)-1)
    _,count,start=strips[index];result=[]
    for i in data['access'][start:start+count]:
        a,b,n,c=data['plates'][i];p=data['points'][a];q=data['points'][b]
        if min(p[0],q[0])<=x<=max(p[0],q[0]) and min(p[1],q[1])<=z<=max(p[1],q[1]):
            nx,ny,nz=data['normals'][n]
            height=Fraction(-(nx*x+nz*z+data['constants'][c]*FX),ny)
            result.append((i,height))
    if len(result)>10:
        raise ValueError('more than ten candidate heights; ambiguous source')
    return result


def tile_candidates(data,x,y):
    if not 0<=x<32 or not 0<=y<32:
        raise ValueError('tile outside32x32 source')
    # MapObject_SetPosDirFromCoords adds half a16-unit tile; collision manager
    # subtracts the16-tile matrix center before CalculateObjectHeight.
    return candidates(data,(x-16)*TILE+TILE//2,(y-16)*TILE+TILE//2)
