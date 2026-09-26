# Builds dex-data.js from the pret/pokeyellow disassembly (Pokémon Yellow's own data tables).
import re, json, os, sys
# Usage: download https://github.com/pret/pokeyellow, then run:
#   python3 build_dex.py path/to/pokeyellow
R = (sys.argv[1] if len(sys.argv) > 1 else 'pokeyellow').rstrip('/') + '/'
rd = lambda p: open(R+p, encoding='utf-8').read()
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
tc = lambda s: ' '.join('-'.join(x.capitalize() for x in w.split('-')) for w in s.split())

# Moves: constant order -> id
consts = re.findall(r'^\s*const (\w+)', rd('constants/move_constants.asm'), re.M)
consts = consts[:consts.index('STRUGGLE')+1]
names = re.findall(r'^\s*li "([^"]+)"', rd('data/moves/names.asm'), re.M)
rows = re.findall(r'^\s*move (\w+),\s*(\w+),\s*(\d+),\s*(\w+),\s*(\d+),\s*(\d+)', rd('data/moves/moves.asm'), re.M)
TYPE = lambda t: 'Psychic' if t == 'PSYCHIC_TYPE' else t.capitalize()
MOVES = []  # index = move id - 1
cid = {}
for i, (c, n, r) in enumerate(zip(consts[1:], names, rows)):
    assert r[0] == c, (c, r)
    MOVES.append([tc(n), TYPE(r[3]), int(r[2]), int(r[4]), int(r[5])])
    cid[c] = i + 1
# TMs / HMs
tms = re.findall(r'^\s*add_tm (\w+)', rd('constants/item_constants.asm'), re.M)
hms = re.findall(r'^\s*add_hm (\w+)', rd('constants/item_constants.asm'), re.M)
assert len(tms) == 50 and len(hms) == 5
TMLIST = [cid[m] for m in tms + hms]  # tm number n -> TMLIST[n-1]; 51..55 = HM01..05

files = re.findall(r'base_stats/(\w+)\.asm', rd('data/pokemon/base_stats.asm'))
assert len(files) == 151
dexno = {norm(f): i + 1 for i, f in enumerate(files)}

# Evolutions & level-up learnsets
evo_src = rd('data/pokemon/evos_moves.asm')
EV, LV = {}, {}
for label, body in re.findall(r'^(\w+)EvosMoves:\n(.*?)(?=^\w+EvosMoves:|\Z)', evo_src, re.M | re.S):
    k = norm(label)
    if k not in dexno: continue
    evos_part, moves_part = body.split('; Learnset')
    ev = []
    for m in re.findall(r'db (EVOLVE_\w+), ([^\n]+)', evos_part):
        a = [x.strip() for x in m[1].split(',')]
        tgt = dexno[norm(a[-1])]
        if m[0] == 'EVOLVE_LEVEL': ev.append(['L', int(a[0]), tgt])
        elif m[0] == 'EVOLVE_ITEM': ev.append(['I', tc(a[0].replace('_', ' ')), tgt])
        else: ev.append(['T', 0, tgt])
    EV[dexno[k]] = ev
    LV[dexno[k]] = [[int(l), cid[mv]] for l, mv in re.findall(r'db (\d+), (\w+)', moves_part)]

# Dex entries: category, height (ft,in), weight (0.1 lb)
DE = {}
for label, cat, ft, inch, wt in re.findall(r'^(\w+)DexEntry:\n\s*db "([^"@]*)@"\n\s*db (\d+),\s*(\d+)\n\s*dw (\d+)', rd('data/pokemon/dex_entries.asm'), re.M):
    if norm(label) in dexno:
        DE[dexno[norm(label)]] = [tc(cat), f"{ft}'{int(inch):02d}\"", int(wt) / 10]

MONS = []
for i, f in enumerate(files):
    s = rd(f'data/pokemon/base_stats/{f}.asm')
    st = list(map(int, re.search(r'db\s+(\d+),\s+(\d+),\s+(\d+),\s+(\d+),\s+(\d+)\s*\n\s*;\s*hp', s).groups()))
    t1, t2 = re.search(r'db (\w+), (\w+) ; type', s).groups()
    types = [TYPE(t1)] + ([TYPE(t2)] if t2 != t1 else [])
    cr = int(re.search(r'db (\d+) ; catch rate', s).group(1))
    bx = int(re.search(r'db (\d+) ; base exp', s).group(1))
    l1 = [cid[m] for m in re.search(r'db ([\w, ]+) ; level 1 learnset', s).group(1).replace(' ', '').split(',') if m != 'NO_MOVE']
    gr = tc(re.search(r'db GROWTH_(\w+)', s).group(1).replace('_', ' '))
    tmblock = re.search(r'tmhm(.*?)\n\s*; end', s, re.S).group(1)
    learn = [m.strip() for m in re.split(r'[,\\\n]', tmblock) if m.strip()]
    tmn = sorted(TMLIST.index(cid[m]) + 1 for m in learn)
    n = i + 1
    MONS.append({'t': types, 'st': st, 'cr': cr, 'bx': bx, 'gr': gr, 'l1': l1,
                 'lv': LV[n], 'tm': tmn, 'ev': EV[n], 'de': DE[n]})

out = ('/* Generated from the pret/pokeyellow disassembly (Pokémon Yellow\'s own data tables).\n'
       '   MOVES[id-1] = [name, type, power, accuracy%, pp]; TM[n-1] = move id (51-55 = HM01-05)\n'
       '   MON[dex-1]: t types, st [hp,atk,def,spd,spc], cr catch rate, bx base exp, gr growth,\n'
       '   l1 moves known at lv1, lv [[level, move]], tm TM/HM numbers, ev [[L|I|T, level|item, dex]],\n'
       '   de [category, height, weight lb] */\n'
       'const DEXDATA=' + json.dumps({'MOVES': MOVES, 'TM': TMLIST, 'MON': MONS}, separators=(',', ':'), ensure_ascii=False) + ';\n')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dex-data.js'), 'w', encoding='utf-8').write(out)
print(len(out), 'bytes;', len(MOVES), 'moves')
