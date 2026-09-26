// render the Nebula theme templates with stub LuCI context (syntax + output check)
'use strict';
import { connect } from 'ubus';
const conn = connect();
const dir = '/tmp/pt/ucode/template/themes/pixel/';
function entityencode(s, attr) { s = replace('' + (s ?? ''), '&', '&amp;'); s = replace(s, '<', '&lt;'); s = replace(s, '>', '&gt;'); if (attr) s = replace(s, '"', '&#34;'); return s; }
function striptags(s) { return replace('' + (s ?? ''), /<[^>]*>/g, ''); }
let scope = {
	dispatcher: { lang: 'en', build_url: (...a) => '/cgi-bin/luci/' + join('/', a), lookup: () => true },
	dispatched: { title: ARGV[1] ?? 'Dashboard' },
	media: '/luci-static/pixel', resource: '/luci-static/resources', node: null, css: null,
	ubus: { call: (o, m, a) => conn.call(o, m, a ?? {}) },
	http: { prepare_content: () => null, getenv: () => '' },
	_: (s) => s, striptags, entityencode,
	ctx: { request_path: split(ARGV[2] ?? 'admin/dashboard', '/') },
	blank_page: ARGV[0] == 'blank',
	version: { distname: 'OpenWrt', distversion: '25.12.5', luciname: 'LuCI', luciversion: '26.267', disturl: 'https://openwrt.org/' },
	lua_active: false, fuser: ARGV[3] == 'fail' ? 'root' : null, duser: 'root'
};
scope.include = (name, sc) => print(render(dir + name + '.ut', { ...scope, ...(sc ?? {}) }));
print(render(dir + ARGV[4] + '.ut', scope));
