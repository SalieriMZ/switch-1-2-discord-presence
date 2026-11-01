// Corre el cliente real de nxapi contra un Discord falso. Sin red y sin tocar el Discord real.
// Uso: node --import <discord-fix.mjs> fake_discord.mjs <absent|closing|silent|restart|restart-closing> <nxapi_dist>
// Sale 0 (GREEN) si la actividad llega al Discord falso; 1 (RED) si no llega a tiempo.
import net from 'node:net';
import { syncBuiltinESMExports } from 'node:module';
import { pathToFileURL } from 'node:url';

const scenario = process.argv[2] || 'absent';
const dist = process.argv[3];
const PIPE = `\\\\?\\pipe\\nso-fake-ipc-${process.pid}`;

const realCreate = net.createConnection;
net.createConnection = (path, cb) => {
  const m = /discord-ipc-(\d+)$/.exec(String(path));
  if (!m) return realCreate(path, cb);
  return realCreate(m[1] === '0' ? PIPE : PIPE + '-none-' + m[1], cb);
};
syncBuiltinESMExports();

const frame = (op, data) => {
  const s = JSON.stringify(data);
  const b = Buffer.alloc(8 + Buffer.byteLength(s));
  b.writeInt32LE(op, 0); b.writeInt32LE(Buffer.byteLength(s), 4); b.write(s, 8);
  return b;
};

let mode = 'off', server = null, activities = 0, sockets = new Set(), connections = 0;
const t0 = Date.now();
const log = (...a) => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s]`, ...a);

function onConn(sock) {
  connections++;
  sockets.add(sock);
  sock.on('close', () => sockets.delete(sock));
  sock.on('error', () => {});
  log('conexión', connections, 'modo', mode);
  if (mode === 'closing') { sock.destroy(); return; }
  sock.on('data', buf => {
    let off = 0;
    while (off + 8 <= buf.length) {
      const op = buf.readInt32LE(off), len = buf.readInt32LE(off + 4);
      const body = buf.subarray(off + 8, off + 8 + len).toString();
      off += 8 + len;
      if (mode === 'silent') continue;
      if (op === 0) {
        sock.write(frame(1, { cmd: 'DISPATCH', evt: 'READY',
          data: { v: 1, config: {}, user: { id: '1', username: 'fake' } } }));
      } else if (op === 1) {
        const msg = JSON.parse(body);
        if (msg.cmd === 'SET_ACTIVITY' && msg.args?.activity) { activities++; log('SET_ACTIVITY recibido'); }
        sock.write(frame(1, { cmd: msg.cmd, nonce: msg.nonce, data: {} }));
      }
    }
  });
}

const listen = () => new Promise(r => { server = net.createServer(onConn); server.listen(PIPE, r); });
const unlisten = () => new Promise(r => {
  for (const s of sockets) s.destroy();
  if (!server) return r();
  server.close(() => { server = null; r(); });
});
const sleep = ms => new Promise(r => setTimeout(r, ms));

process.on('unhandledRejection', e => log('unhandledRejection', e?.message));
process.on('uncaughtException', e => log('uncaughtException', e?.message));

const { ZncDiscordPresence } = await import(pathToFileURL(`${dist}/common/presence.js`).href);
const Client = Object.getPrototypeOf(new ZncDiscordPresence({}, null).discord).constructor;
const client = new Client({ discord_client_filter: undefined, discord_preconnect: false, presence_enabled: true });

const finish = ok => { log(ok ? 'GREEN' : 'RED', `escenario=${scenario} conexiones=${connections} actividades=${activities}`); process.exit(ok ? 0 : 1); };
const waitActivity = async (n, ms) => { const end = Date.now() + ms; while (Date.now() < end) { if (activities >= n) return true; await sleep(100); } return activities >= n; };

const activity = { id: '950883021165330493', activity: { details: 'Test', type: 0 } };

if (scenario === 'restart' || scenario === 'restart-closing') {
  mode = 'healthy'; await listen();
  await client.setActivity(activity);
  if (!await waitActivity(1, 5000)) finish(false);
  log('Discord se cierra'); await unlisten();
  if (scenario === 'restart-closing') { mode = 'closing'; await listen(); }
  await sleep(7000);
  await unlisten();
  log('Discord vuelve'); mode = 'healthy'; await listen();
  finish(await waitActivity(2, 15000));
} else {
  // Discord aún no abre o está arrancando...
  if (scenario !== 'absent') { mode = scenario; await listen(); }
  await client.setActivity(activity);
  await sleep(scenario === 'silent' ? 12000 : 6000);
  // ...y luego queda listo.
  await unlisten();
  log('Discord listo'); mode = 'healthy'; await listen();
  finish(await waitActivity(1, 15000));
}
