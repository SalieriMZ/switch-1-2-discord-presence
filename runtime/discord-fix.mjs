// Se carga con `node --import` antes de nxapi. Vive fuera de node_modules: sobrevive a "Actualizar nxapi".
//
// discord-rpc espera el evento 'close' para terminar transport.close(). Si Discord ya cerró la conexión
// (pasa mientras arranca), ese evento ya ocurrió y la promesa no termina nunca: nxapi deja de reintentar
// y la actividad no llega a Discord hasta reiniciar la presencia.
import { createRequire } from 'node:module';

const CLOSE_TIMEOUT_MS = 2000;

try {
    const require = createRequire(new URL('./node_modules/nxapi/package.json', import.meta.url));
    const { prototype } = require('discord-rpc/src/transports/ipc.js');
    const close = prototype.close;

    prototype.close = function () {
        const socket = this.socket;
        if (!socket || socket.destroyed) return Promise.resolve();
        return Promise.race([
            close.call(this),
            new Promise(resolve => setTimeout(() => {
                socket.destroy();
                resolve();
            }, CLOSE_TIMEOUT_MS).unref()),
        ]);
    };
} catch (err) {
    // Una versión futura de nxapi puede mover este archivo: mejor sin el arreglo que sin presencia.
    console.warn('discord-fix: no se pudo aplicar:', err.message);
}
