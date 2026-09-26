// read [[obj, method, args], ...] as JSON on stdin, print results array
'use strict';
import { stdin, popen } from 'fs';
import { connect } from 'ubus';
let conn = connect();
let reqs = json(stdin.read('all'));
let out = [];
for (let r in reqs) {
	if (r[0] == '@exec') {
		let f = popen(r[1], 'r');
		let s = f ? f.read('all') : '';
		let rc = f ? f.close() : 1;
		push(out, [0, { code: rc, stdout: s }]);
		continue;
	}
	let res = conn.call(r[0], r[1], r[2] ?? {});
	let err = conn.error(true);
	push(out, res == null ? [ err ?? 4 ] : [0, res]);
}
print(out, "\n");
