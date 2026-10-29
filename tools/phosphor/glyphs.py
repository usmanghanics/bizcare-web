"""Reads TrueType glyph outlines and prints them as SVG path data.

Usage: python3 -I glyphs.py FONT.ttf CODEPOINT_HEX [...] > out.json
Writes {"e0ee": {"d": "...", "box": 256}, ...} scaled to a 256 unit box,
y pointing down, like Phosphor's own SVGs.
"""
import json
import struct
import sys


class Font:
    def __init__(self, path):
        self.b = open(path, 'rb').read()
        n = struct.unpack_from('>H', self.b, 4)[0]
        self.t = {}
        for i in range(n):
            tag, _, off, ln = struct.unpack_from('>4sIII', self.b, 12 + 16 * i)
            self.t[tag.decode('latin1')] = (off, ln)
        head = self.t['head'][0]
        self.upem = struct.unpack_from('>H', self.b, head + 18)[0]
        self.loc_long = struct.unpack_from('>h', self.b, head + 50)[0] == 1
        hhea = self.t['hhea'][0]
        self.ascent, self.descent = struct.unpack_from('>hh', self.b, hhea + 4)
        self.num_glyphs = struct.unpack_from('>H', self.b, self.t['maxp'][0] + 4)[0]
        self.cmap = self._cmap()

    def _cmap(self):
        base = self.t['cmap'][0]
        n = struct.unpack_from('>H', self.b, base + 2)[0]
        best = None
        for i in range(n):
            pid, eid, off = struct.unpack_from('>HHI', self.b, base + 4 + 8 * i)
            fmt = struct.unpack_from('>H', self.b, base + off)[0]
            if fmt in (4, 12) and (best is None or fmt == 12):
                best = (fmt, base + off)
        fmt, o = best
        m = {}
        if fmt == 12:
            groups = struct.unpack_from('>I', self.b, o + 12)[0]
            for g in range(groups):
                s, e, gid = struct.unpack_from('>III', self.b, o + 16 + 12 * g)
                for cp in range(s, e + 1):
                    m[cp] = gid + cp - s
        else:
            segx2 = struct.unpack_from('>H', self.b, o + 6)[0]
            seg = segx2 // 2
            ends = struct.unpack_from('>%dH' % seg, self.b, o + 14)
            starts = struct.unpack_from('>%dH' % seg, self.b, o + 16 + segx2)
            deltas = struct.unpack_from('>%dh' % seg, self.b, o + 16 + 2 * segx2)
            ro_at = o + 16 + 3 * segx2
            ros = struct.unpack_from('>%dH' % seg, self.b, ro_at)
            for i in range(seg):
                for cp in range(starts[i], ends[i] + 1):
                    if cp == 0xFFFF:
                        continue
                    if ros[i] == 0:
                        gid = (cp + deltas[i]) & 0xFFFF
                    else:
                        a = ro_at + 2 * i + ros[i] + 2 * (cp - starts[i])
                        gid = struct.unpack_from('>H', self.b, a)[0]
                        if gid:
                            gid = (gid + deltas[i]) & 0xFFFF
                    m[cp] = gid
        return m

    def _glyph_range(self, gid):
        loca = self.t['loca'][0]
        if self.loc_long:
            a, b = struct.unpack_from('>II', self.b, loca + 4 * gid)
        else:
            a, b = struct.unpack_from('>HH', self.b, loca + 2 * gid)
            a, b = a * 2, b * 2
        return self.t['glyf'][0] + a, b - a

    def contours(self, gid, dx=0, dy=0):
        """Each contour as a list of (x, y, on_curve)."""
        o, ln = self._glyph_range(gid)
        if ln == 0:
            return []
        nc = struct.unpack_from('>h', self.b, o)[0]
        if nc < 0:
            return self._composite(o + 10, dx, dy)
        p = o + 10
        ends = struct.unpack_from('>%dH' % nc, self.b, p)
        p += 2 * nc
        ilen = struct.unpack_from('>H', self.b, p)[0]
        p += 2 + ilen
        count = ends[-1] + 1 if nc else 0
        flags = []
        while len(flags) < count:
            f = self.b[p]
            p += 1
            flags.append(f)
            if f & 8:
                r = self.b[p]
                p += 1
                flags.extend([f] * r)
        def coords(short_bit, same_bit):
            nonlocal p
            out, v = [], 0
            for f in flags:
                if f & short_bit:
                    d = self.b[p]
                    p += 1
                    v += d if f & same_bit else -d
                elif not f & same_bit:
                    v += struct.unpack_from('>h', self.b, p)[0]
                    p += 2
                out.append(v)
            return out
        xs = coords(2, 16)
        ys = coords(4, 32)
        res, start = [], 0
        for e in ends:
            res.append([(xs[i] + dx, ys[i] + dy, bool(flags[i] & 1)) for i in range(start, e + 1)])
            start = e + 1
        return res

    def _composite(self, p, dx, dy):
        res = []
        while True:
            flags, gid = struct.unpack_from('>HH', self.b, p)
            p += 4
            if flags & 1:
                a1, a2 = struct.unpack_from('>hh', self.b, p)
                p += 4
            else:
                a1, a2 = struct.unpack_from('>bb', self.b, p)
                p += 2
            if flags & 8:
                p += 2
            elif flags & 0x40:
                p += 4
            elif flags & 0x80:
                p += 8
            res += self.contours(gid, dx + a1, dy + a2)
            if not flags & 0x20:
                return res


def path(font, contours):
    s = 256 / (font.ascent - font.descent)
    def pt(x, y):
        return '%s %s' % (fmt((x) * s), fmt((font.ascent - y) * s))
    out = []
    for c in contours:
        if not c:
            continue
        # Start on an on-curve point, or the midpoint of two off-curve ones.
        k = next((i for i, q in enumerate(c) if q[2]), None)
        if k is None:
            a, b = c[0], c[1]
            first = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, True)
            pts = c + []
            c = [first] + pts
        else:
            c = c[k:] + c[:k]
        out.append('M' + pt(c[0][0], c[0][1]))
        ctrl = None
        for q in c[1:] + [c[0]]:
            if q[2]:
                if ctrl is None:
                    out.append('L' + pt(q[0], q[1]))
                else:
                    out.append('Q' + pt(*ctrl[:2]) + ' ' + pt(q[0], q[1]))
                    ctrl = None
            else:
                if ctrl is not None:
                    mid = ((ctrl[0] + q[0]) / 2, (ctrl[1] + q[1]) / 2)
                    out.append('Q' + pt(*ctrl[:2]) + ' ' + pt(*mid))
                ctrl = q
        out.append('Z')
    return ''.join(out)


def fmt(v):
    r = round(v, 1)
    return ('%d' % r) if r == int(r) else ('%.1f' % r)


if __name__ == '__main__':
    font = Font(sys.argv[1])
    result = {}
    for hexcp in sys.argv[2:]:
        gid = font.cmap.get(int(hexcp, 16))
        if gid is None:
            print('missing', hexcp, file=sys.stderr)
            continue
        result[hexcp] = {'d': path(font, font.contours(gid)), 'box': 256}
    print(json.dumps(result))
    print('upem', font.upem, 'ascent', font.ascent, 'descent', font.descent, file=sys.stderr)
