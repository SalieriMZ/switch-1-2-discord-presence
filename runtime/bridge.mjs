// Puente entre la app Python y nxapi para lo que la CLI no expone de forma no interactiva.
// Cada comando imprime UNA línea JSON en stdout. Errores: {"error": "..."} y exit 1.
//
//   node bridge.mjs auth-url                       -> {"url", "state_file"}
//   node bridge.mjs auth-complete <state_file> <link> -> {"id","nickname","screen_name","nso_name"}
//   node bridge.mjs whoami                         -> {...} | null   (solo storage local, sin red)

import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(here, 'node_modules', 'nxapi', 'dist');
// getToken/initStorage/paths no están en el mapa "exports" de nxapi: se importan por ruta de archivo.
const load = (rel) => import(pathToFileURL(path.join(dist, rel)).href);

function out(value) {
    process.stdout.write(JSON.stringify(value) + '\n');
}

async function storage() {
    const { initStorage } = await load('util/storage.js');
    const { paths } = await load('util/product.js');
    return initStorage(process.env.NXAPI_DATA_PATH || paths.data);
}

function describe(saved, id) {
    return {
        id: saved?.user?.id ?? id,
        nickname: saved?.user?.nickname ?? null,
        screen_name: saved?.user?.screenName ?? null,
        nso_name: saved?.nsoAccount?.user?.name ?? null,
    };
}

async function authUrl() {
    const { NintendoAccountSessionAuthorisationCoral } = await load('api/coral.js');
    const auth = NintendoAccountSessionAuthorisationCoral.create();
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'nso-rpc-auth-'));
    const state_file = path.join(dir, 'auth.json');
    await fs.writeFile(state_file, JSON.stringify({
        url: auth.authorise_url, state: auth.state, verifier: auth.verifier,
    }), { mode: 0o600 });
    out({ url: auth.authorise_url, state_file });
}

async function authComplete(state_file, link) {
    if (!state_file || !link) throw new Error('uso: auth-complete <state_file> <link>');
    const { NintendoAccountSessionAuthorisationCoral } = await load('api/coral.js');
    const { getToken } = await load('common/auth/coral.js');

    const saved = JSON.parse(await fs.readFile(state_file, 'utf-8'));
    const auth = NintendoAccountSessionAuthorisationCoral.resume(saved.url, saved.state, saved.verifier);
    const params = new URLSearchParams(new URL(link).hash.slice(1));
    const token = await auth.getSessionToken(params);

    // Igual que `nxapi nso auth` (src/cli/nso/auth.ts).
    const store = await storage();
    const { data } = await getToken(store, token.session_token);
    await store.setItem('NintendoAccountToken.' + data.user.id, token.session_token);
    const users = new Set(await store.getItem('NintendoAccountIds') ?? []);
    users.add(data.user.id);
    await store.setItem('NintendoAccountIds', [...users]);
    await store.setItem('SelectedUser', data.user.id);

    await fs.rm(path.dirname(state_file), { recursive: true, force: true });
    out(describe(data, data.user.id));
}

async function whoami() {
    const store = await storage();
    const id = await store.getItem('SelectedUser');
    if (!id) return out(null);
    const token = await store.getItem('NintendoAccountToken.' + id);
    if (!token) return out(null);
    out(describe(await store.getItem('NsoToken.' + token), id));
}

const [cmd, ...args] = process.argv.slice(2);
const commands = { 'auth-url': authUrl, 'auth-complete': authComplete, whoami };

try {
    if (!commands[cmd]) throw new Error('comando desconocido: ' + cmd);
    await commands[cmd](...args);
} catch (err) {
    out({ error: err?.message ?? String(err) });
    process.exitCode = 1;
}
