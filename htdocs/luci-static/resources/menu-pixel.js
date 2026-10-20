'use strict';
'require baseclass';
'require ui';
'require rpc';
'require poll';
'require pixel.ui as pui';

/*
 * luci-theme-pixel menu: sidebar navigation, breadcrumbs, tab menus, the
 * hostname wordmark and a small live readout (memory, load, uptime) taken from
 * the standard "system info" ubus call. Licensed under the Apache License 2.0.
 */

const callSystemInfo = rpc.declare({ object: 'system', method: 'info', expect: { '': {} } });

const CAT_ICONS = {
	status: 'status', system: 'system', services: 'services', network: 'network', vpn: 'vpn',
	statistics: 'activity', nas: 'storage', docker: 'chip', control: 'lock', modem: 'wifi', dashboard: 'dashboard'
};

function store(key, value) {
	try {
		if (value === undefined)
			return JSON.parse(localStorage.getItem(key) || 'null');
		localStorage.setItem(key, JSON.stringify(value));
	}
	catch (e) {}
	return null;
}

return baseclass.extend({
	__init__() {
		this.bindChrome();
		this.renderBrand();
		ui.menu.load().then((tree) => this.render(tree));
	},

	/* the hostname in the display font; it decodes out of noise once per session */
	renderBrand() {
		const slot = document.getElementById('px-wm');
		if (!slot)
			return;
		let boot = false;
		try { boot = !sessionStorage.getItem('pixel.boot'); sessionStorage.setItem('pixel.boot', '1'); } catch (e) {}
		const full = (slot.textContent || '').trim();
		const name = pui.wmName(full) || 'OPENWRT';
		const room = (slot.parentNode.clientWidth || 280) - 44;
		slot.replaceChildren(pui.fitWordmark(name, room, { boot: boot, period: 9, max: 2 }));
		slot.title = full;
		const sub = document.getElementById('px-brand-sub');
		if (sub) {
			/* "Xiaomi Redmi Router AX6000 (OpenWrt U-Boot layout)" -> "Redmi Router AX6000":
			   notes in brackets go first, then the vendor if it is still long; two lines at most */
			const model = sub.textContent.replace(/^\s*>\s*/, '').trim();
			let text = model.replace(/\s*\([^)]*\)/g, '').trim() || model;
			if (text.length > 18) text = text.replace(/^\S+\s+/, '');
			if (text.length > 34) text = text.slice(0, 33) + '…';
			sub.title = model;
			sub.replaceChildren(E('b', {}, [ '> ' ]), pui.typed(text, { delay: boot ? 1.2 : 0, instant: !boot }));
		}
	},

	bindChrome() {
		const body = document.body;
		document.getElementById('px-burger')?.addEventListener('click', () => body.classList.toggle('px-menu-open'));
		document.getElementById('px-scrim')?.addEventListener('click', () => body.classList.remove('px-menu-open'));
		document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') body.classList.remove('px-menu-open'); });

		const btn = document.getElementById('px-theme');
		if (btn && window.pixelTheme) {
			const order = [ 'auto', 'dark', 'light' ];
			const names = { auto: 'Theme: automatic', dark: 'Theme: dark', light: 'Theme: light' };
			const paint = () => {
				const cur = window.pixelTheme();
				btn.replaceChildren(pui.icon(cur === 'auto' ? 'auto' : (cur === 'dark' ? 'moon' : 'sun')));
				btn.title = names[cur];
			};
			btn.addEventListener('click', () => {
				const cur = window.pixelTheme();
				window.pixelTheme(order[(order.indexOf(cur) + 1) % order.length]);
				paint();
			});
			paint();
		}
	},

	render(tree) {
		const modes = ui.menu.getChildren(tree);
		let mode = modes[0];

		modes.forEach((m) => {
			if (L.env.requestpath.length && m.name === L.env.requestpath[0])
				mode = m;
		});

		if (mode) {
			this.renderNav(mode);
			this.renderCrumbs(mode);
		}

		if (L.env.dispatchpath.length >= 3) {
			let node = tree, url = '';
			for (let i = 0; i < 3 && node; i++) {
				node = node.children[L.env.dispatchpath[i]];
				url = url + (url ? '/' : '') + L.env.dispatchpath[i];
			}
			if (node)
				this.renderTabMenu(node, url);
		}

		this.startReadout();
	},

	renderNav(mode) {
		const nav = document.getElementById('px-nav');
		if (!nav)
			return;

		const openState = store('pixel.nav') || {};
		const singles = E('ul'), groups = E('ul');

		ui.menu.getChildren(mode).forEach((cat) => {
			if (cat.name === 'logout')
				return;

			const catActive = L.env.dispatchpath[1] === cat.name;
			const children = ui.menu.getChildren(cat);
			const icon = pui.icon(CAT_ICONS[cat.name] || 'services');

			if (!children.length) {
				if (!cat.action || cat.action.type === 'firstchild')
					return;
				singles.appendChild(E('li', { 'class': catActive ? 'active' : '' }, [
					E('a', { 'href': L.url(mode.name, cat.name) }, [ icon, E('span', {}, [ _(cat.title) ]) ])
				]));
				return;
			}

			const isOpen = (cat.name in openState) ? openState[cat.name] : catActive;
			const sub = E('ul');

			children.forEach((page) => {
				const pageActive = catActive && L.env.dispatchpath[2] === page.name;
				sub.appendChild(E('li', { 'class': pageActive ? 'active' : '' }, [
					E('a', { 'href': L.url(mode.name, cat.name, page.name) }, [ _(page.title) ])
				]));
			});

			const btn = E('button', { 'type': 'button', 'aria-expanded': isOpen ? 'true' : 'false' }, [
				icon, E('span', {}, [ _(cat.title) ]), pui.icon('chevron', 'px-chev')
			]);
			const li = E('li', { 'class': 'px-group' + (catActive ? ' active' : '') + (isOpen ? ' open' : '') }, [
				btn, E('div', { 'class': 'px-sub' }, [ sub ])
			]);

			btn.addEventListener('click', () => {
				const open = li.classList.toggle('open');
				btn.setAttribute('aria-expanded', open ? 'true' : 'false');
				const st = store('pixel.nav') || {};
				st[cat.name] = open;
				store('pixel.nav', st);
			});

			groups.appendChild(li);
		});

		const label = (n, t) => E('div', { 'class': 'px-nav-label' }, [ E('em', {}, [ n ]), E('i', {}, [ '/' ]), t ]);
		if (singles.children.length)
			nav.appendChild(label('01', _('Overview')));
		nav.appendChild(singles);
		if (groups.children.length)
			nav.appendChild(label(singles.children.length ? '02' : '01', _('Menu')));
		nav.appendChild(groups);
	},

	renderCrumbs(mode) {
		const box = document.getElementById('px-crumbs');
		if (!box)
			return;

		let node = mode;
		const parts = [];

		for (let i = 1; i < L.env.dispatchpath.length && node; i++) {
			node = node.children?.[L.env.dispatchpath[i]];
			if (node?.title)
				parts.push(_(node.title));
		}

		if (!parts.length)
			parts.push(_(mode.title));

		parts.forEach((p, i) => {
			if (i)
				box.appendChild(E('span', { 'class': 'px-sep' }, [ '/' ]));
			box.appendChild(E('span', {}, [ p ]));
		});
	},

	renderTabMenu(tree, url, level) {
		const container = document.querySelector('#tabmenu');
		const ul = E('ul', { 'class': 'tabs' });
		const children = ui.menu.getChildren(tree);
		let activeNode = null;

		children.forEach((child) => {
			const isActive = (L.env.dispatchpath[3 + (level || 0)] == child.name);

			ul.appendChild(E('li', { 'class': 'tabmenu-item-%s %s'.format(child.name, isActive ? 'active' : '') }, [
				E('a', { 'href': L.url(url, child.name) }, [ _(child.title) ])
			]));

			if (isActive)
				activeNode = child;
		});

		if (ul.children.length == 0)
			return E([]);

		container.appendChild(ul);
		container.style.display = '';

		if (activeNode)
			this.renderTabMenu(activeNode, url + '/' + activeNode.name, (level || 0) + 1);

		return ul;
	},

	/* memory, load and uptime in the sidebar footer and the top bar */
	startReadout() {
		const foot = document.getElementById('px-side-foot');
		const top = document.getElementById('px-glance');
		if (!foot && !top)
			return;

		this.ro = {
			mem: E('b', {}, [ '–' ]), memM: E('span', {}, [ pui.meter(0) ]),
			load: E('b', {}, [ '–' ]), loadM: E('span', {}, [ pui.meter(0) ]),
			up: E('b', {}, [ '–' ])
		};
		if (foot)
			foot.appendChild(E('div', { 'class': 'px-sysline' }, [
				E('span', { 'title': _('Memory usage') }, [ 'mem' ]), this.ro.memM, this.ro.mem,
				E('span', { 'title': _('Load average') }, [ 'load' ]), this.ro.loadM, this.ro.load
			]));
		if (top) {
			this.ro.topUp = E('b', {}, [ '–' ]);
			top.appendChild(E('span', { 'class': 'px-gl px-opt', 'title': _('Uptime') }, [ E('i', {}, [ 'up' ]), this.ro.topUp ]));
		}

		const tick = () => callSystemInfo().then((s) => this.paintReadout(s)).catch(() => {
			foot?.classList.add('px-hidden');
		});
		tick();
		poll.add(tick, 5);
	},

	paintReadout(s) {
		if (!s || !s.memory)
			return;
		const m = s.memory, avail = m.available ?? ((m.free || 0) + (m.buffered || 0) + (m.cached || 0));
		const pct = m.total ? Math.round((m.total - avail) / m.total * 100) : 0;
		const load = (s.load?.[0] ?? 0) / 65536;
		this.ro.mem.textContent = pct + '%';
		this.ro.memM.replaceChildren(pui.meter(pct));
		this.ro.load.textContent = load.toFixed(2);
		this.ro.loadM.replaceChildren(pui.meter(Math.min(100, load * 50)));
		if (this.ro.topUp)
			this.ro.topUp.textContent = pui.dur(s.uptime);
	}
});
