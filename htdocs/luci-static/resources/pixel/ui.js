'use strict';
'require baseclass';

/*
 * luci-theme-pixel helpers: 9x9 pixel icons, the 12-row display font of
 * github.com/Trendorin for wordmarks (decoding out of pixel noise, with a
 * glint), typed text with a block cursor and segmented meters. Everything is
 * drawn with crisp SVG rectangles. Licensed under the Apache License 2.0.
 */

const SVGNS = 'http://www.w3.org/2000/svg';

/* 9x9 icons, "#" = pixel */
const ICONS = {
	dashboard: '####.#### #..#.#..# #..#.#### #..#..... ####.#### .....#..# ####.#..# #..#.#..# ####.####',
	devices: '#####.... #...#.... #...#.### #####.#.# ..#...#.# .###..#.# ......#.# ......### .........',
	status: '......... ...#..... ...##.... ..#.#.... ###.#..## ....#..#. .....#.#. .....##.. ......#..',
	activity: '......... ...#..... ...##.... ..#.#.... ###.#..## ....#..#. .....#.#. .....##.. ......#..',
	system: '......... .##...... ######### .##...... ......... ......##. ######### ......##. .........',
	services: '######### #.#.....# ######### ......... ######### #.#.....# ######### ......... .........',
	network: '...###... ...#.#... ...###... ....#.... .#######. .#.....#. ###...### #.#...#.# ###...###',
	vpn: '######### #.......# #.......# #.......# #.......# .#.....#. ..#...#.. ...#.#... ....#....',
	shield: '######### #.......# #.......# #.......# #.......# .#.....#. ..#...#.. ...#.#... ....#....',
	'shield-check': '######### #.......# #.....#.# #....#..# #.#.#...# .#.#...#. ..#...#.. ...#.#... ....#....',
	'shield-alert': '######### #.......# #...#...# #...#...# #...#...# .#.....#. ..#.#.#.. ...#.#... ....#....',
	'shield-off': '#.####### .#......# #.#.....# #..#....# #...#...# .#...#.#. ..#...#.. ...#.#.#. ....#...#',
	logout: '####..... #........ #.....#.. #......#. #..###### #......#. #.....#.. #........ ####.....',
	sun: '....#.... .#.....#. ...###... ..#####.. #.#####.# ..#####.. ...###... .#.....#. ....#....',
	moon: '..####... .##...... ##....... ##....... ##....... ##......# .##....## ..######. .........',
	auto: '..#####.. .#...###. #....#### #....#### #....#### #....#### #....#### .#...###. ..#####..',
	chevron: '......... ......... .#.....#. ..#...#.. ...#.#... ....#.... ......... ......... .........',
	'chevron-right': '......... ..#...... ...#..... ....#.... .....#... ....#.... ...#..... ..#...... .........',
	x: '......... .#.....#. ..#...#.. ...#.#... ....#.... ...#.#... ..#...#.. .#.....#. .........',
	check: '......... ........# .......#. ......#.. #....#... .#..#.... ..##..... ...#..... .........',
	plus: '......... ....#.... ....#.... ....#.... .#######. ....#.... ....#.... ....#.... .........',
	menu: '......... ######### ......... ......... ######### ......... ......... ######### .........',
	wifi: '.#######. #.......# ..#####.. .#.....#. ...###... ..#...#.. ......... ....#.... .........',
	ethernet: '######### #.......# #.#.#.#.# #.#.#.#.# #.......# #.......# ###...### ..#...#.. ..#####..',
	down: '....#.... ....#.... ....#.... ....#.... #...#...# .#..#..#. ..#.#.#.. ...###... ....#....',
	up: '....#.... ...###... ..#.#.#.. .#..#..#. #...#...# ....#.... ....#.... ....#.... ....#....',
	thermometer: '...###... ...#.#... ...#.#... ...#.#... ...###... ..#####.. .#######. .#######. ..#####..',
	cpu: '..#.#.#.. .#######. ##.....## .#.###.#. ##.###.## .#.###.#. ##.....## .#######. ..#.#.#..',
	memory: '......... ######### #.#.#.#.# #.#.#.#.# #.......# ######### .#.#.#.#. .#.#.#.#. .........',
	storage: '......... ..#####.. .#.....#. #.......# ######### #.......# #.##....# ######### .........',
	clock: '..#####.. .#.....#. #...#...# #...#...# #...###.# #.......# #.......# .#.....#. ..#####..',
	lock: '..#####.. .#.....#. .#.....#. ######### #.......# #...#...# #...#...# #.......# #########',
	globe: '..#####.. .#..#..#. #..#.#..# ######### #..#.#..# ######### #..#.#..# .#..#..#. ..#####..',
	ban: '..#####.. .#.....#. #.#.....# #..#....# #...#...# #....#..# #.....#.# .#.....#. ..#####..',
	unplug: '..#...#.. ..#...#.. .#######. .#.....#. .#.....#. ..#...#.. ...###... ....#.... ....#....',
	pencil: '......##. .....#..# ....#..#. ...#..#.. ..#..#... .#..#.... #..#..... ##....... .........',
	gauge: '..#####.. .#.....#. #.....#.# #....#..# #...#...# #.......# .#.....#. ......... .........',
	trash: '...###... ######### .#.....#. .#.#.#.#. .#.#.#.#. .#.#.#.#. .#.#.#.#. .#.....#. ..#####..',
	search: '.####.... #....#... #....#... #....#... #....#... .#####... ......#.. .......#. ........#',
	refresh: '..####.#. .#....##. #....###. #........ #.......# ........# .###....# .##....#. .#.####..',
	alert: '....#.... ...#.#... ...#.#... ..#.#.#.. ..#.#.#.. .#..#..#. .#.....#. #...#...# #########',
	info: '..#####.. .#.....#. #...#...# #.......# #..##...# #...#...# #..###..# .#.....#. ..#####..',
	router: '.#.....#. .#.....#. .#.....#. .#.....#. ######### #.......# #.#.#.#.# #.......# #########',
	users: '...###... ..#...#.. ..#...#.. ...###... ......... .#######. #.......# #.......# .........',
	smartphone: '..#####.. ..#...#.. ..#...#.. ..#...#.. ..#...#.. ..#...#.. ..#####.. ..#.#.#.. ..#####..',
	tablet: '.#######. .#.....#. .#.....#. .#.....#. .#.....#. .#.....#. .#######. .#..#..#. .#######.',
	laptop: '......... .#######. .#.....#. .#.....#. .#.....#. .#######. #.......# ######### .........',
	tv: '..#...#.. ...#.#... ######### #.......# #.......# #.......# #.......# ######### .........',
	monitor: '######### #.......# #.......# #.......# #.......# ######### ....#.... ..#####.. .........',
	speaker: '.#######. .#..#..#. .#.....#. .#.###.#. .##...##. .##...##. .#.###.#. .#.....#. .#######.',
	chip: '.#.#.#.#. ######### .#.....#. ##.#.#.## .#..#..#. ##.#.#.## .#.....#. ######### .#.#.#.#.',
	filter: '######### .#.....#. ..#...#.. ...#.#... ...#.#... ...#.#... ...#.#... ...#.#... ...###...',
	arrow: '......... .....#... ......#.. .......#. ######### .......#. ......#.. .....#... .........',
	key: '......... ......... .###..... #...#.... #...##### #...#.#.# .###..#.# ......... .........',
	eye: '......... ..#####.. .#.....#. #..###..# #..###..# .#.....#. ..#####.. ......... .........',
	fingerprint: '..#####.. .#.....#. #..###..# #.#...#.# #.#.#.#.# #.#.#.#.# ..#.#.#.. ..#.#.... ....#....',
	zap: '......#.. .....##.. ....##... ...##.... ..######. ....##... ...##.... ..##..... ..#......',
	power: '....#.... .#..#..#. #...#...# #...#...# #.......# #.......# .#.....#. ..#####.. .........',
	terminal: '######### #.......# #.#.....# #..#....# #.#..##.# #.......# ######### ......... .........',
	pin: '..#####.. .#.....#. #..###..# #..###..# .#.....#. ..#...#.. ...#.#... ....#.... .........',
	dot: '......... ......... ......... ...###... ...###... ...###... ......... ......... .........'
};

/* 12-row display font of the profile header ("*n" repeats a row) */
const BIG = {
	A: '.########. ########## ##......##*3 ##########*2 ##......##*5',
	B: '#########. ########## ##......##*3 #########.*2 ##......##*3 ########## #########.',
	C: '.######### ########## ##........*8 ########## .#########',
	D: '#########. ########## ##......##*8 ########## #########.',
	E: '#########*2 ##.......*3 #######..*2 ##.......*3 #########*2',
	F: '#########*2 ##.......*3 #######..*2 ##.......*5',
	G: '.######### ########## ##........*3 ##...#####*2 ##......##*3 ########## .#########',
	H: '##......##*5 ##########*2 ##......##*5',
	I: '##*12',
	J: '.......##*9 ##.....## ######### .#######.',
	K: '##......## ##.....##. ##....##.. ##...##... ##..##.... #####.....*2 ##..##.... ##...##... ##....##.. ##.....##. ##......##',
	L: '##.......*10 #########*2',
	M: '###......### ####....#### ##.##..##.## ##..####..## ##...##...## ##........##*7',
	N: '###.....##*2 ####....##*2 ##.##...##*2 ##..##..##*2 ##...##.##*2 ##....####*2',
	O: '.########. ########## ##......##*8 ########## .########.',
	P: '#########. ########## ##......##*3 ########## #########. ##........*5',
	Q: '.########. ########## ##......##*6 ##...##.## ##....#### ########## .#######.#',
	R: '#########. ########## ##......##*3 ########## #########. ##...##... ##....##.. ##.....##. ##......##*2',
	S: '.######### ########## ##........*3 #########. .######### ........##*3 ########## #########.',
	T: '##########*2 ....##....*10',
	U: '##......##*10 ########## .########.',
	V: '##......##*8 .##....##. ..##..##.. ...####... ....##....',
	W: '##........##*7 ##...##...## ##..####..## ##.##..##.## ####....#### ###......###',
	X: '##......##*2 .##....##. ..##..##.. ...####... ....##....*2 ...####... ..##..##.. .##....##. ##......##*2',
	Y: '##......##*2 .##....##. ..##..##.. ...####... ....##....*7',
	Z: '##########*2 .......##. ......##.. .....##... ....##.... ...##..... ..##...... .##....... ##........ ##########*2',
	0: '.########. ########## ##......##*3 ##..##..##*2 ##......##*3 ########## .########.',
	1: '####.. ####.. ..##..*8 ######*2',
	2: '#########. ########## ........##*3 .######### #########. ##........*3 ##########*2',
	3: '#########. ########## ........##*3 ..########*2 ........##*3 ########## #########.',
	4: '##......##*5 ##########*2 ........##*5',
	5: '##########*2 ##........*3 #########. ########## ........##*3 ########## #########.',
	6: '.######### ########## ##........*3 #########. ########## ##......##*3 ########## .########.',
	7: '##########*2 ........##*10',
	8: '.########. ########## ##......##*3 .########. ########## ##......##*3 ########## .########.',
	9: '.########. ########## ##......##*3 ########## .######### ........##*3 ########## #########.',
	' ': '.....*12',
	'-': '......*5 ######*2 ......*5',
	'.': '..*10 ##*2',
	'!': '##*9 ..*1 ##*2'
};

const cache = {};

function rows(spec, big) {
	const key = (big ? 'B' : 'S') + spec;
	if (cache[key])
		return cache[key];
	const out = [];
	spec.split(' ').forEach((tok) => {
		const [ row, n ] = tok.split('*');
		for (let i = 0; i < (+n || 1); i++)
			out.push(row);
	});
	return (cache[key] = out);
}

/* merge pixels of a bitmap into horizontal runs: "M x y h w v s h -w z" */
function runsPath(grid, s, ox, oy, pick) {
	let d = '';
	grid.forEach((row, y) => {
		let x = 0;
		while (x < row.length) {
			if (!pick(row[x])) { x++; continue; }
			let n = 1;
			while (x + n < row.length && pick(row[x + n]))
				n++;
			d += 'M' + (ox + x * s) + ' ' + (oy + y * s) + 'h' + (n * s) + 'v' + s + 'h' + (-n * s) + 'z';
			x += n;
		}
	});
	return d;
}

function S(tag, attrs) {
	const el = document.createElementNS(SVGNS, tag);
	for (const k in attrs || {})
		el.setAttribute(k, attrs[k]);
	return el;
}

function svgBox(w, h, cls, label) {
	const s = S('svg', { 'viewBox': '0 0 ' + w + ' ' + h, 'width': w, 'height': h, 'class': cls || '', 'shape-rendering': 'crispEdges' });
	if (label) { s.setAttribute('role', 'img'); s.setAttribute('aria-label', label); }
	else s.setAttribute('aria-hidden', 'true');
	return s;
}

let uid = 0;
const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

return baseclass.extend({
	SVGNS: SVGNS,
	S: S,
	runsPath: runsPath,

	icon(name, cls) {
		const grid = rows(ICONS[name] || ICONS.dot);
		const s = svgBox(9, 9, cls ? 'px-ico ' + cls : 'px-ico');
		s.removeAttribute('width');
		s.removeAttribute('height');
		s.appendChild(S('path', { 'd': runsPath(grid, 1, 0, 0, (c) => c === '#'), 'fill': 'currentColor' }));
		return s;
	},

	bigWidth(text, gap) {
		let w = 0;
		String(text).toUpperCase().split('').forEach((ch) => { w += rows(BIG[ch] || BIG[' '], true)[0].length + (gap ?? 2); });
		return Math.max(0, w - (gap ?? 2));
	},

	/*
	 * Wordmark in the profile's display font. With boot=true every letter slot
	 * flickers through pixel noise and settles in turn; a glint then sweeps
	 * across the letters every few seconds. Rows above the cut are bright,
	 * rows below dim, with a one-pixel shadow: the two-tone "chrome" cut.
	 */
	wordmark(text, u, opts) {
		opts = opts || {};
		const up = String(text).toUpperCase();
		const gap = 2, cut = 7, id = 'wm' + (++uid);
		const tw = this.bigWidth(up, gap);
		const W = (tw + 1) * u, H = 13 * u;
		const svg = svgBox(W, H, 'px-wm' + (opts.cls ? ' ' + opts.cls : ''), up);
		const boot = opts.boot && !reduced();
		const frame = 0.07, frames = 5, t0 = opts.delay || 0.1;
		const css = [];
		let x = 0, i = 0, letters = '';

		up.split('').forEach((ch) => {
			const g = rows(BIG[ch] || BIG[' '], true);
			const w = g[0].length, ox = x * u;
			const start = t0 + i * 0.1, settle = start + frame * frames;
			const hide = boot ? { 'style': 'animation-duration:' + settle.toFixed(2) + 's' } : {};
			if (boot && ch !== ' ') {
				for (let k = 0; k < frames; k++) {
					const noise = g.map((r) => r.split('').map(() => (Math.random() < 0.3 ? '#' : '.')).join(''));
					svg.appendChild(S('path', { 'class': 'nz', 'd': runsPath(noise, u, ox, 0, (c) => c === '#'),
						'style': 'animation-delay:' + (start + k * frame).toFixed(2) + 's' }));
				}
			}
			const sh = runsPath(g, u, ox + u, u, (c) => c === '#');
			const hi = runsPath(g.slice(0, cut), u, ox, 0, (c) => c === '#');
			const lo = runsPath(g.slice(cut), u, ox, cut * u, (c) => c === '#');
			if (sh) svg.appendChild(S('path', Object.assign({ 'class': 'sh' + (boot ? ' h' : ''), 'd': sh }, hide)));
			if (hi) svg.appendChild(S('path', Object.assign({ 'class': 'hi' + (boot ? ' h' : ''), 'd': hi }, hide)));
			if (lo) svg.appendChild(S('path', Object.assign({ 'class': 'lo' + (boot ? ' h' : ''), 'd': lo }, hide)));
			letters += runsPath(g, u, ox, 0, (c) => c === '#');
			x += w + gap;
			i++;
		});

		/* glint: a slanted band clipped to the letters, stepping one pixel at a time */
		if (opts.glint !== false && !reduced()) {
			const sweep = W + 16 * u, steps = Math.round(sweep / u);
			const ready = boot ? t0 + i * 0.1 + frame * frames + 0.5 : 1.5;
			let band = '';
			for (let r = 0; r < 12; r++)
				band += 'M' + (-8 * u + Math.floor((11 - r) / 2) * u) + ' ' + (r * u) + 'h' + (2 * u) + 'v' + u + 'h' + (-2 * u) + 'z';
			const defs = S('defs');
			const clip = S('clipPath', { 'id': id + 'c' });
			clip.appendChild(S('path', { 'd': letters }));
			defs.appendChild(clip);
			svg.insertBefore(defs, svg.firstChild);
			const g = S('g', { 'clip-path': 'url(#' + id + 'c)' });
			g.appendChild(S('path', { 'class': 'gl', 'd': band,
				'style': 'animation:' + id + 'g ' + (opts.period || 7) + 's ' + ready.toFixed(2) + 's infinite' }));
			svg.appendChild(g);
			css.push('@keyframes ' + id + 'g{0%{transform:translateX(0);animation-timing-function:steps(' + steps + ',end)}14%,100%{transform:translateX(' + sweep + 'px)}}');
		}
		if (css.length) {
			const st = S('style');
			st.textContent = css.join('');
			svg.insertBefore(st, svg.firstChild);
		}
		return svg;
	},

	/* text that types itself; the cursor keeps blinking at the end */
	typed(text, opts) {
		opts = opts || {};
		const el = E('span', { 'class': 'px-typed' + (opts.cls ? ' ' + opts.cls : '') });
		const speed = opts.speed || 0.028, delay = opts.delay || 0;
		const chars = Array.from(String(text));
		if (reduced() || opts.instant) {
			el.appendChild(document.createTextNode(text));
		}
		else {
			chars.forEach((ch, i) => {
				el.appendChild(E('span', { 'style': 'animation-duration:' + (delay + i * speed).toFixed(3) + 's' }, [ ch ]));
			});
		}
		if (opts.cursor !== false)
			el.appendChild(E('i', { 'class': 'px-cursor', 'style': 'animation-delay:' + (reduced() || opts.instant ? 0 : (delay + chars.length * speed)).toFixed(2) + 's' }));
		return el;
	},

	/* "01 / NETWORK" section label between dotted rules */
	label(num, text) {
		return E('div', { 'class': 'px-label' }, [
			E('span', {}, [
				num != null ? E('em', {}, [ String(num).padStart(2, '0') ]) : '',
				num != null ? E('i', {}, [ '/' ]) : '',
				text
			])
		]);
	},

	/* segmented meter: 12 blocks, lit up to pct */
	meter(pct, cls) {
		const n = 12, lit = Math.round(Math.max(0, Math.min(100, pct || 0)) / 100 * n);
		return E('span', { 'class': 'px-meter' + (cls ? ' ' + cls : ''), 'title': Math.round(pct || 0) + '%' },
			Array.from({ length: n }, (_, i) => E('i', { 'class': i < lit ? 'on' : '' })));
	},

	/* bytes -> "12.4 MB" */
	bytes(n) {
		const u = [ 'B', 'KB', 'MB', 'GB', 'TB' ];
		let v = Math.max(0, +n || 0), i = 0;
		while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
		return (i == 0 || v >= 100 ? v.toFixed(0) : v.toFixed(1)) + ' ' + u[i];
	},

	/* seconds -> "3d 4h", "2h 15m", "4m 10s" */
	dur(s) {
		s = Math.max(0, Math.floor(+s || 0));
		const d = Math.floor(s / 86400), h = Math.floor(s / 3600) % 24, m = Math.floor(s / 60) % 60, sec = s % 60;
		if (d) return d + 'd ' + h + 'h';
		if (h) return h + 'h ' + m + 'm';
		if (m) return m + 'm ' + sec + 's';
		return sec + 's';
	}
});
