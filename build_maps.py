# Builds maps-data.js (the detailed location maps) from the pret/pokeyellow disassembly.
# Usage: download https://github.com/pret/pokeyellow, then run:
#   python3 build_maps.py path/to/pokeyellow
# Each 16x16 walking square of every map becomes one letter:
#   . floor   g tall grass   w water   t tree   k cuttable tree   r rock/cliff
#   b building   f fence/post   x indoor wall   v/l/e ledge (jump down / left / right)
import re, os, sys, json
R = (sys.argv[1] if len(sys.argv) > 1 else 'pokeyellow').rstrip('/') + '/'
rd = lambda p: open(R + p, encoding='utf-8').read()
hexi = lambda s: int(s.strip().replace('$', '0x'), 0)
tc = lambda s: ' '.join('-'.join(x.capitalize() for x in w.split('-')) for w in s.split())

# Blocked outdoor squares, sorted into trees / rocks / buildings etc. (key = its four 8x8 tile ids)
CLASSES = {"Forest": {"default": "t", "patterns": {"01012929": "b", "08091819": "b", "09091919": "b", "090c191c": "b", "1a1b4b4c": "b", "21223132": "f", "28293829": "b", "292c293c": "b", "42424343": "f"}}, "Overworld": {"default": "b", "patterns": {"01011111": "r", "02392402": "r", "07071717": "r", "0d240d24": "t", "0d243734": "t", "0e0e5555": "f", "11111111": "r", "14141414": "w", "14331414": "w", "14541454": "w", "17172222": "r", "1d241d24": "t", "1d243734": "t", "231e1e27": "r", "24242424": "t", "27272727": "r", "272c272c": "r", "272c3637": "t", "27363637": "r", "2a2b3a3b": "f", "2c2c3734": "t", "2c2c3737": "t", "2d2e3d3e": "k", "31311414": "w", "32143214": "w", "33141414": "w", "33331414": "t", "33331454": "w", "33333214": "w", "34243734": "t", "35372435": "t", "37131327": "t", "37373737": "t", "39393637": "t", "39393737": "t", "3c3c043c": "f", "40415051": "t"}}, "Plateau": {"default": "r", "patterns": {"07081718": "t", "090a191a": "f", "10122829": "f", "14141414": "t", "141f1414": "t", "141f141f": "t", "25262829": "f", "32141414": "t", "32143214": "t", "33331414": "t", "3d3d3d3d": "b", "3d443d44": "b", "3e3e3d3d": "b", "3e413d44": "b", "403e443d": "b", "443d443d": "b"}}}

# ---- maps: constants, sizes, block files, headers ----
MAPC = [(m[0], int(m[1]), int(m[2])) for m in re.findall(r'^\s*map_const (\w+),\s*(\d+),\s*(\d+)', rd('constants/map_constants.asm'), re.M)]
MAPID = {c: i for i, (c, w, h) in enumerate(MAPC)}
BLK, pend = {}, []
for line in rd('maps.asm').splitlines():
    pend += re.findall(r'(\w+)_Blocks:', line)
    m = re.search(r'INCBIN "([^"]+)"', line)
    if m:
        for l in pend: BLK[l] = m.group(1)
        pend = []
HDR = {}
for f in sorted(os.listdir(R + 'data/maps/headers')):
    s = rd('data/maps/headers/' + f)
    m = re.search(r'map_header (\w+), (\w+), (\w+)', s)
    if m:
        HDR[m.group(2)] = dict(name=m.group(1), tileset=m.group(3),
                               conns={d: c for d, _, c, o in re.findall(r'connection (\w+), (\w+), (\w+), (-?\d+)', s)})

# ---- tilesets: blockset file, collision (walkable) tiles, grass tile ----
camel2const = lambda n: re.sub(r'(?<!^)(?=[A-Z]|(?<![0-9])[0-9])', '_', n).upper()
TSN = re.findall(r'^\s*tileset (\w+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),', rd('data/tilesets/tileset_headers.asm'), re.M)
TS = {}
lines = rd('gfx/tilesets.asm').splitlines()
for n, a, b, c, g in TSN:
    for j, l in enumerate(lines):
        if l.startswith(n + '_Block::'):
            k = j
            while 'INCBIN' not in lines[k]: k += 1
            TS[n] = dict(blk=re.search(r'INCBIN "([^"]+)"', lines[k]).group(1), grass=None if g.strip() == '-1' else hexi(g))
cur = []
for l in rd('data/tilesets/collision_tile_ids.asm').splitlines():
    m = re.match(r'(\w+)_Coll::', l)
    if m: cur.append(m.group(1)); continue
    if 'coll_tiles' in l and cur:
        ids = {hexi(x) for x in l.split('coll_tiles')[1].split(',') if x.strip()}
        for c in cur: TS[c]['coll'] = ids
        cur = []
TSBYCONST = {camel2const(n): n for n in TS}
WATER_TS = set(re.findall(r'db (\w+)', rd('data/tilesets/water_tilesets.asm').split('ShoreTiles')[0]))
BS = {}
def blockset(ts):
    if ts not in BS:
        d = open(R + TS[ts]['blk'], 'rb').read(); BS[ts] = [d[i:i + 16] for i in range(0, len(d), 16)]
    return BS[ts]
LEDGE = {0x36: 'v', 0x37: 'v', 0x27: 'l', 0x0D: 'e', 0x1D: 'e'}

def grid(const):
    h = HDR[const]; w, hh = [(x[1], x[2]) for x in MAPC if x[0] == const][0]
    tsc = h['tileset']; ts = TSBYCONST[tsc]; bs = blockset(ts); blk = open(R + BLK[h['name']], 'rb').read()
    coll, grass = TS[ts]['coll'], TS[ts]['grass']
    cl = CLASSES.get(ts)
    out = []
    if len(blk) < w * hh: blk += blk[-w:][:w * hh - len(blk)]  # one map's file is a few blocks short; repeat its last row
    for sy in range(hh * 2):
        row = []
        for sx in range(w * 2):
            b = bs[blk[(sy // 2) * w + sx // 2]]
            o = (sy % 2) * 8 + (sx % 2) * 2
            t4 = (b[o], b[o + 1], b[o + 4], b[o + 5]); bl = t4[2]
            if bl in coll: ch = 'g' if bl == grass else '.'
            elif bl == 0x14 and tsc in WATER_TS: ch = 'w'
            elif ts == 'Overworld' and bl in LEDGE: ch = LEDGE[bl]
            elif cl: ch = cl['patterns'].get(''.join('%02x' % t for t in t4), cl['default'])
            elif ts == 'Cavern': ch = 'r'
            else: ch = 'x'
            row.append(ch)
        out.append(''.join(row))
    return w * 2, hh * 2, out

def rle(rows):
    s = ''.join(rows); out = []; i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]: j += 1
        out.append(s[i] + (str(j - i) if j - i > 1 else '')); i = j
    return ''.join(out)

# ---- names ----
def pretty(m):
    t = tc(m.replace('_', ' ')).replace('Pokecenter', 'Pokémon Center').replace('Mart', 'Poké Mart').replace('Ss Anne', 'S.S. Anne') \
        .replace('Mt Moon', 'Mt. Moon').replace('Pokemon', 'Pokémon').replace('Silph Co ', 'Silph Co. ')
    t = re.sub(r'\b(B?\d+)f\b', lambda x: x.group(1).upper() + 'F', t, flags=re.I)
    t = t.replace('Hall Of Fame', 'Hall of Fame').replace('Mr Psychic', 'Mr. Psychic').replace('Mr Fuji', 'Mr. Fuji').replace(' Gate 1F', ' Gate').replace('Ss ', 'S.S. ')
    return re.sub(r"\b(Oak|Lorelei|Bruno|Agatha|Lance|Champion|Diglett|Red|Blue|Bill|Fuji|Warden|Copycat|Rater|Psychic|Guard|Melanie|Daisy|Bruno)s\b", r"\1's", t)
ITEMNAMES = {}
for i, c in enumerate(re.findall(r'^\s*const (\w+)', rd('constants/item_constants.asm').split('NUM_ITEMS')[0], re.M)):
    ITEMNAMES[c] = i
NAMES = [tc(n.replace('é', 'e')) for n in re.findall(r'^\s*li "([^"]+)"', rd('data/items/names.asm'), re.M)]
TMLIST = re.findall(r'^\s*add_tm (\w+)', rd('constants/item_constants.asm'), re.M)
HMLIST = re.findall(r'^\s*add_hm (\w+)', rd('constants/item_constants.asm'), re.M)
MOVENAMES = dict(zip(re.findall(r'^\s*const (\w+)', rd('constants/move_constants.asm'), re.M)[1:],
                     [tc(n) for n in re.findall(r'^\s*li "([^"]+)"', rd('data/moves/names.asm'), re.M)]))
NICE_ITEM = {'Hp Up': 'HP Up', 'Pp Up': 'PP Up', 'Poke Ball': 'Poké Ball', 'Elixer': 'Elixir', 'Max Elixer': 'Max Elixir', 'X Special': 'X Special'}
def item_name(c):
    m = re.fullmatch(r'TM_(\w+)', c)
    if m and m.group(1) in TMLIST: return 'TM%02d %s' % (TMLIST.index(m.group(1)) + 1, MOVENAMES.get(m.group(1), ''))
    m = re.fullmatch(r'HM_(\w+)', c)
    if m and m.group(1) in HMLIST: return 'HM%02d %s' % (HMLIST.index(m.group(1)) + 1, MOVENAMES.get(m.group(1), ''))
    nm = NAMES[ITEMNAMES[c] - 1] if c in ITEMNAMES and 0 < ITEMNAMES[c] <= len(NAMES) else tc(c.replace('_', ' '))
    return NICE_ITEM.get(nm, nm)
dexc = re.findall(r'^\s*const (DEX_\w+)', rd('constants/pokedex_constants.asm'), re.M)
MONS = {d[4:]: i + 1 for i, d in enumerate(dexc)}

# ---- toggleable objects (item balls etc. that disappear once taken) ----
TOG = {}; tmap = None; ti = 0
for l in rd('data/maps/toggleable_objects.asm').split('ToggleableObjectStates:')[1].splitlines():
    m = re.match(r'\s*toggleable_objects_for (\w+)', l)
    if m: tmap = m.group(1); continue
    m = re.match(r'\s*toggle_object_state (\w+),', l)
    if m: TOG[m.group(1)] = ti; ti += 1

# ---- trainers: text label -> beaten flag ----
def trainer_events(name):
    p = 'scripts/%s.asm' % name
    if not os.path.exists(R + p): return {}
    s = rd(p); hdr = dict(re.findall(r'^(\w+TrainerHeader\d+):\s*\n\s*trainer (EVENT_\w+)', s, re.M))
    txt = dict((b, a) for a, b in re.findall(r'dw_const (\w+),\s*(TEXT_\w+)', s))
    out = {}
    for const, label in txt.items():
        m = re.search(r'^' + label + r':\s*\n((?:.*\n){0,6})', s, re.M)
        if not m: continue
        body = m.group(1)
        h = re.search(r'ld hl, (\w+TrainerHeader\d+)', body)
        if h and h.group(1) in hdr: out[const] = hdr[h.group(1)][6:]; continue
        e = re.search(r'CheckEvent (EVENT_BEAT_\w+)', body)
        if e: out[const] = e.group(1)[6:]
    return out

# ---- hidden items ----
HID = [(m[0], int(m[1]), int(m[2])) for m in re.findall(r'hidden_item (\w+),\s*(\d+),\s*(\d+)', rd('data/events/hidden_item_coords.asm'))]
HEV = {}
for block in re.split(r'\n\s*hidden_events_for ', rd('data/events/hidden_events.asm'))[1:]:
    mp = block.split('\n', 1)[0].strip()
    for x, y, it in re.findall(r'hidden_event\s+(\d+),\s*(\d+), HiddenItems, (\w+)', block): HEV[(mp, int(x), int(y))] = it

# ---- which tracker location each map belongs to ----
TOWNS = {'PALLET_TOWN': 'pallet', 'VIRIDIAN_CITY': 'viridian', 'PEWTER_CITY': 'pewter', 'CERULEAN_CITY': 'cerulean', 'LAVENDER_TOWN': 'lavender',
         'VERMILION_CITY': 'vermilion', 'CELADON_CITY': 'celadon', 'FUCHSIA_CITY': 'fuchsia', 'CINNABAR_ISLAND': 'cinnabar', 'SAFFRON_CITY': 'saffron'}
DUNGEON = [('VIRIDIAN_FOREST', 'vforest'), ('MT_MOON_POKECENTER', ''), ('MT_MOON', 'mtmoon'), ('ROCK_TUNNEL_POKECENTER', ''), ('ROCK_TUNNEL', 'rtunnel'),
           ('POWER_PLANT', 'power'), ('POKEMON_TOWER', 'tower'), ('SS_ANNE', 'ssanne'), ('DIGLETTS_CAVE', 'diglett'), ('SAFARI_ZONE', 'safari'),
           ('SEAFOAM_ISLANDS', 'seafoam'), ('VICTORY_ROAD', 'victory'), ('CERULEAN_CAVE', 'ccave'), ('LORELEIS_ROOM', 'indigo'), ('BRUNOS_ROOM', 'indigo'),
           ('AGATHAS_ROOM', 'indigo'), ('LANCES_ROOM', 'indigo'), ('CHAMPIONS_ROOM', 'indigo'), ('HALL_OF_FAME', 'indigo'), ('INDIGO_PLATEAU', 'indigo')]
def base_loc(m):
    if m in TOWNS: return TOWNS[m]
    r = re.fullmatch(r'ROUTE_(\d+)', m)
    if r: return 'r' + r.group(1)
    for pre, loc in DUNGEON:
        if m.startswith(pre): return loc
    return ''

# leftover warps from development that can't be reached in the game
JUNK_WARPS = {('REDS_HOUSE_2F', 'SILPH_CO_11F')}
TRAINER_FIX = {('SILPH_CO_11F', 'Giovanni'): 'BEAT_SILPH_CO_GIOVANNI', ('ROUTE_24', 'Rocket'): 'BEAT_ROUTE24_ROCKET',
               ('FIGHTING_DOJO', 'Blackbelt'): 'BEAT_KARATE_MASTER'}

# ---- parse every map ----
MAPS = {}
for const, h in HDR.items():
    name = h['name']; p = 'data/maps/objects/%s.asm' % name
    if not os.path.exists(R + p) or name not in BLK: continue
    s = rd(p)
    G = grid(const)
    if not G: continue
    w, hh, rows = G
    warps = [(int(x), int(y), d) for x, y, d, n in re.findall(r'warp_event\s+(\d+),\s*(\d+),\s*(\w+),\s*(\d+)', s)
             if (const, d) not in JUNK_WARPS]
    consts = re.findall(r'const_export (\w+)', s)
    tev = trainer_events(name)
    objs = []
    for i, m in enumerate(re.finditer(r'object_event\s+(\d+),\s*(\d+),\s*(SPRITE_\w+),\s*(\w+),\s*(\w+),\s*(TEXT_\w+)(?:,\s*(\w+))?(?:,\s*(\w+))?', s)):
        x, y, spr, mv, fc, text, a7, a8 = m.groups(); x, y = int(x), int(y)
        oc = consts[i] if i < len(consts) else ''
        tog = TOG.get(oc, -1)
        if a7 and a7.startswith('OPP_'):
            tn = re.sub(r'Rival\d', 'Rival', tc(a7[4:].replace('_', ' ')).replace(' ', ' '))
            tn = re.sub(r'\s*\d$', '', tn).replace('Lt Surge', 'Lt. Surge').replace('Jr Trainer', 'Jr. Trainer').replace('Psychic Tr', 'Psychic')
            objs.append([x, y, 't', tn, tev.get(text, '') or TRAINER_FIX.get((const, tn), ''), tog])
        elif spr == 'SPRITE_POKE_BALL':
            if a7 and a7 in MONS: objs.append([x, y, 'm', MONS[a7], tog])
            elif a7:
                nm = item_name(a7); objs.append([x, y, 'i', NICE_ITEM.get(nm, nm), tog])
            else:
                gift = [k for k in MONS if re.search(r'_' + k + r'_POKE_?BALL$', text)]
                if gift: objs.append([x, y, 'm', MONS[gift[0]], tog, 1])
                else: objs.append([x, y, 'p', tog])
        elif spr == 'SPRITE_BOULDER': objs.append([x, y, 'o', tog])
        elif a7 and a7 in MONS: objs.append([x, y, 'm', MONS[a7], tog])
        else: objs.append([x, y, 'p', tog])
    hid = [[x, y, item_name(HEV.get((const, x, y), 'NO_ITEM')), i] for i, (mc, x, y) in enumerate(HID) if mc == const]
    MAPS[const] = dict(n=pretty(const), loc=base_loc(const), w=w, h=hh, rows=rows, wp=warps, o=objs, hi=hid, cn=h['conns'])

# indoor maps belong to the place you walk in from (nearest first)
queue = [c for c in sorted(MAPS, key=lambda c: MAPID[c]) if MAPS[c]['loc']]
while queue:
    c = queue.pop(0)
    for x, y, d in MAPS[c]['wp']:
        if d in MAPS and not MAPS[d]['loc']: MAPS[d]['loc'] = MAPS[c]['loc']; queue.append(d)
ids = sorted(MAPS, key=lambda c: MAPID[c])
idx = {c: i for i, c in enumerate(ids)}
out = []
for c in ids:
    M = MAPS[c]
    out.append({'id': MAPID[c], 'n': M['n'], 'loc': M['loc'], 'w': M['w'], 'h': M['h'], 'g': rle(M['rows']),
                'wp': [[x, y, idx[d] if d in idx else -1] for x, y, d in M['wp']], 'o': M['o'], 'hi': M['hi'],
                'cn': {k[0]: idx[v] for k, v in M['cn'].items() if v in idx}})
js = ('/* Generated by build_maps.py from the pret/pokeyellow disassembly: a simplified plan of every map.\n'
      '   g: one letter per 16x16 walking square, run-length encoded (see build_maps.py for the letters)\n'
      '   wp: doors/stairs [x, y, destination map index or -1 = back outside]; cn: neighbouring maps\n'
      '   o: objects [x, y, t=trainer(class, beaten flag, toggle) | i=item(name, toggle) | m=Pokémon(dex, toggle) | o=boulder | p=person]\n'
      '   hi: hidden items [x, y, name, found-flag bit] */\n'
      'const MAPDATA=' + json.dumps(out, separators=(',', ':'), ensure_ascii=False) + ';\n')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maps-data.js'), 'w', encoding='utf-8').write(js)
print(len(js), 'bytes;', len(out), 'maps;', sum(len(M['o']) for M in MAPS.values()), 'objects;', sum(len(M['hi']) for M in MAPS.values()), 'hidden items')

# ============================================================
# Real map pictures (maps-img.js): every map drawn tile by tile from the
# game's own tileset graphics, in its Game Boy Color palette. Needs Pillow.
# ============================================================
import base64, io
from PIL import Image
GFX, pend = {}, []
for l in rd('gfx/tilesets.asm').splitlines():
    pend += re.findall(r'(\w+)_GFX::', l)
    m = re.search(r'INCBIN "([^"]+)\.2bpp"', l)
    if m and pend:
        for n in pend: GFX[n] = m.group(1) + '.png'
        pend = []
# Game Boy Color background palettes, by name (PAL_ROUTE, PAL_PALLET, ...)
cgb = rd('data/sgb/sgb_palettes.asm').split('CGBBasePalettes:')[1]
PAL = {}
for m in re.finditer(r'RGB ([\d, ]+);\s*(PAL_\w+)', cgb):
    v = [int(x) for x in m.group(1).split(',')]
    PAL.setdefault(m.group(2), [tuple(round(c * 255 / 31) for c in v[i:i + 3]) for i in range(0, 12, 3)])
PAL_ORDER = [n for n in re.findall(r';\s*(PAL_\w+)', cgb)]
CITY_PALS = PAL_ORDER[1:12]  # PAL_PALLET ... PAL_SAFFRON, in map order
LOC_TOWN = {v: k for k, v in TOWNS.items()}
def map_palette(const):
    ts = TSBYCONST[HDR[const]['tileset']]
    if ts == 'Cemetery' or const in ('TRADE_CENTER', 'COLOSSEUM'): return PAL['PAL_GRAYMON']
    if ts == 'Cavern' or const.startswith('CERULEAN_CAVE') or const == 'BRUNOS_ROOM': return PAL['PAL_CAVE']
    if const == 'LORELEIS_ROOM': return PAL['PAL_PALLET']
    town = const if MAPID[const] < len(CITY_PALS) else LOC_TOWN.get(MAPS[const]['loc'])
    if MAPID[const] < MAPID['ROUTE_1'] or (MAPID[const] >= MAPID[[c for c, _, _ in MAPC if c.startswith('REDS_HOUSE')][0]] and town):
        if town and MAPID[town] < len(CITY_PALS): return PAL[CITY_PALS[MAPID[town]]]
    return PAL['PAL_ROUTE']
TILES = {}
def tiles(ts):
    if ts not in TILES:
        im = Image.open(R + GFX[ts]).convert('L'); cols = im.width // 8
        T = [im.crop((i % cols * 8, i // cols * 8, i % cols * 8 + 8, i // cols * 8 + 8)) for i in range(cols * (im.height // 8))]
        if ts == 'Overworld':  # the flower tile is animated in the game; use its first frame
            T[3] = Image.open(R + 'gfx/tilesets/flower/flower1.png').convert('L')
        TILES[ts] = T
    return TILES[ts]
def picture(const):
    h = HDR[const]; w, hh = [(x[1], x[2]) for x in MAPC if x[0] == const][0]
    ts = TSBYCONST[h['tileset']]; bs = blockset(ts); T = tiles(ts)
    blk = open(R + BLK[h['name']], 'rb').read()
    if len(blk) < w * hh: blk += blk[-w:][:w * hh - len(blk)]
    im = Image.new('L', (w * 32, hh * 32), 255)
    blank = Image.new('L', (8, 8), 255)
    for by in range(hh):
        for bx in range(w):
            b = bs[blk[by * w + bx]]
            for k in range(16):
                im.paste(T[b[k]] if b[k] < len(T) else blank, (bx * 32 + k % 4 * 8, by * 32 + k // 4 * 8))
    pal = map_palette(const)
    out = im.point(lambda v: 3 - round(v / 85)).convert('P')
    out.putpalette([c for rgb in pal for c in rgb] + [0] * (768 - 12))
    buf = io.BytesIO(); out.save(buf, 'PNG', optimize=True, bits=2)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
imgs = [picture(c) for c in ids]
js = ('/* Generated by build_maps.py: a picture of every map (same order as MAPDATA), drawn from the\n'
      '   game\'s own tiles in its Game Boy Color palette. 16 pixels = one walking square. */\n'
      'const MAPIMG=' + json.dumps(imgs, separators=(',', ':')) + ';\n')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maps-img.js'), 'w').write(js)
print(len(js), 'bytes of map pictures')
