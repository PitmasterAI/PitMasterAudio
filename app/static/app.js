'use strict';

// mismos ajustes destacados que la app: Claro y Retro (fijos)
const DESTACADOS = ['base_claro', 'base_retro'];

// Lo que falle en el navegador se manda al servidor: así se puede mirar qué pasa en
// un equipo al que no se llega (Windows, otro Linux) sin depender de que se vea.
const AVISAR = (dato) => {
  try {
    fetch('/api/consola', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.assign({
        cuando: new Date().toISOString(),
        navegador: navigator.userAgent,
        pantalla: window.innerWidth + 'x' + window.innerHeight,
      }, dato)),
    }).catch(() => {});
  } catch (e) { /* sin conexión */ }
};
window.addEventListener('error', (e) => {
  AVISAR({ tipo: 'error', mensaje: String(e.message), fichero: e.filename, linea: e.lineno });
});
window.addEventListener('unhandledrejection', (e) => {
  AVISAR({ tipo: 'promesa', mensaje: String(e.reason && e.reason.name || e.reason) });
});
const $ = (s) => document.querySelector(s);

const S = {
  id: null, preset: null, presets: [], viendoOriginal: false, pidiendo: false,
  medidasOriginal: null, medidasMaster: null, presetNombre: null,
  picosOriginal: null, picosMaster: null,
  auto: null, autoLufs: {}, autoActivo: true, fijoActivo: true,
  elMaster: null, presetSonando: null,
  intensidad: 100, lufs: -10, calculando: new Set(), hechos: new Set(),
  pendientes: 0, ultimoTrabajo: 0, nativo: false
};

const signo = (v) => (v > 0 ? '+' : '') + Number(v).toFixed(1);
// la app escribe los números de los textos con coma decimal
const coma = (v, dec) => Number(v).toFixed(dec).replace('.', ',');

// misma frase que la app: «Amplificador · -12,2 LUFS · pico -0,30 dBTP»
function fmtSonando(titulo, lufs, tp) {
  if (lufs === undefined || lufs === null) return titulo;
  if (tp === undefined || tp === null) return `${T(titulo)} · ${coma(lufs, 1)} LUFS`;
  return `${T(titulo)} · ${coma(lufs, 1)} LUFS · ${T('pico')} ${coma(tp, 2)} dBTP`;
}

// misma frase que la app: «-16.4 LUFS · cresta 16.8 dB · estéreo 0.87 · graves +4.4 dB · agudos -6.8 dB»
function fmtPerfil(p) {
  if (!p) return '';
  return `${coma(p.lufs, 1)} LUFS · cresta ${coma(p.cresta, 1)} dB · ` +
    `estéreo ${coma(p.correlacion, 2)} · ${T('graves')} ${signo(p.graves_db).replace('.', ',')} dB · ` +
    `${T('agudos')} ${signo(p.agudos_db).replace('.', ',')} dB`;
}

// «Motor principal: GPU» / «Motor secundario: CPU», como en la app
async function mirarMotores() {
  try {
    const j = await (await fetch('/api/motor')).json();
    $('#motorPrincipal').textContent = T('Motor principal: ') + j.principal;
    $('#motorSecundario').textContent = T('Motor secundario: ') + j.secundario;
  } catch (e) { /* se queda el texto por defecto */ }
}



/**
 * El panel arranca en blanco: no se retoma la canción de la vez anterior ni se
 * queda sonando nada de una sesión vieja. Se decide así expresamente.
 */
async function arrancarEnLimpio() {
  S.id = null;
  S.presets = [];
  S.hechos = new Set();
  S.calculando = new Set();
  S.medidasOriginal = null;
  S.medidasMaster = null;
  S.picosOriginal = null;
  S.picosMaster = null;
  S.presetSonando = null;
  S.presetNombre = null;
  S.preset = null;
  S.sugerido = '';
  S.pidiendo = false;
  S.viendoOriginal = true;
  try {
    const j = await (await fetch('/api/repro/estado')).json();
    REPRO.leer(j);
    if (j && j.sonando) await REPRO.mando('parar');   // nada suena al abrir
  } catch (e) { /* sin sonido propio */ }
  REPRO.pos = 0;
  REPRO.dur = 0;
  ['#panelTema', '#panelOpciones', '#cajaRecomendada'].forEach((sel) => {
    const el = $(sel);
    if (el) el.classList.add('oculto');
  });
  $('#nombreTema').textContent = T('Ningún audio elegido');
  $('#perfilAudio').textContent = T('Sube una canción para verlo');
  $('#pistaRecomendado').textContent = '';
  $('#detalleTema').textContent = '';
  $('#estadoTrabajo').textContent = '';
  $('#btnDescargar').setAttribute('href', '#');
  marcarMasterListo(false);
  $('#audioOriginal').src = '';
  $('#audioMaster').src = '';
  $('#audioMaster2').src = '';
  dibujarOnda(new Array(220).fill(0.06), 0);
}

// ------------------------------------------------------------------ idioma
/** Pinta la recomendación con el nombre traducido. */
function pintarPista() {
  const nombre = S.sugerido || '';
  $('#pistaRecomendado').textContent = (nombre && nombre !== 'Claro')
    ? `${T('Por cómo suena, encaja ')}${T(nombre)}${T('. Empiezas con Claro; cámbialo cuando quieras.')}`
    : T('Empiezas con Claro; cámbialo cuando quieras.');
}

/** Banderas: la del idioma activo en rosa. */
function pintarBanderas() {
  document.querySelectorAll('#banderas .bandera').forEach((b) => {
    b.classList.toggle('activa', b.dataset.idioma === IDIOMA.valor);
  });
}

/** Traduce los textos fijos que hay escritos en el HTML. */
function traducirNodos(raiz) {
  const paseo = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, null);
  const cambios = [];
  let nodo = paseo.nextNode();
  while (nodo) {
    const padre = nodo.parentNode && nodo.parentNode.nodeName;
    if (padre !== 'SCRIPT' && padre !== 'STYLE') {
      const texto = nodo.nodeValue;
      const limpio = (texto || '').trim();
      if (limpio) {
        const nuevo = T(limpio);
        if (nuevo !== limpio) cambios.push([nodo, texto.replace(limpio, nuevo)]);
      }
    }
    nodo = paseo.nextNode();
  }
  cambios.forEach(([n, valor]) => { n.nodeValue = valor; });
}

/**
 * Cambia todos los textos al idioma elegido SIN recargar ni tocar el audio
 * (el sonido lo lleva el servidor, así que aquí solo se repinta la pantalla).
 */
function aplicarIdioma() {
  document.documentElement.lang = IDIOMA.valor;
  traducirNodos(document.body);
  pintarBanderas();
  mirarMotores();
  if (S.sugerido !== undefined) pintarPista();
  if (S.id) {
    pintarOpciones();
    pintarSonando();
  }
  $('#btnAuto').textContent = T(S.autoActivo ? 'Auto ✓' : 'Auto');
  $('#btnFijo').textContent = T(S.fijoActivo ? 'Fijo ✓' : 'Fijo');
  ponerIntensidad(S.intensidad);
  const finos = $('#detalleFinos');
  $('#resumenFinos').textContent = T(finos.open ? 'Ajustes finos ▾' : 'Ajustes finos ▸');
  if (S.pidiendo) {
    $('#estadoTrabajo').textContent = `${T('Aplicando ')}${T(S.presetNombre || S.preset || '')}…`;
  }
}

/** Si al reabrir no ha arrancado en 1,2 s, se reintenta una vez. */
function vigilarArranque() {
  if (!S.nativo) return;
  setTimeout(() => {
    if (!REPRO.sonando && REPRO.dur > 0) REPRO.seguir();
  }, 1200);
}

// ------------------------------------------------------------------ subir
async function subir(archivo) {
  const fd = new FormData();
  fd.append('audio', archivo);
  $('#nombreTema').textContent = archivo.name;
  $('#perfilAudio').textContent = T('Analizando…');
  $('#barraSubida').classList.remove('quieta');
  try {
    const r = await fetch('/api/subir', { method: 'POST', body: fd });
    let d;
    try {
      d = await r.json();
    } catch (e) {
      d = { error: T('El servidor no ha entendido el archivo (¿está dañado?)') };
    }
    if (!r.ok || d.error) {
      $('#perfilAudio').textContent = T(d.error) || T('No se ha podido leer el audio');
      $('#nombreTema').textContent = archivo.name;
      return;
    }
    S.id = d.id;
    S.hechos = new Set();
    S.calculando = new Set();
    S.presetSonando = null;
    S.medidasMaster = null;
    S.picosOriginal = null;
    S.picosMaster = null;
    S.viendoOriginal = true;
    marcarMasterListo(false);
    // los dos reproductores de masterizado empiezan de cero con la canción nueva
    $('#audioMaster').src = '';
    $('#audioMaster2').src = '';
    $('#audioMaster').classList.add('oculto');
    $('#audioMaster2').classList.add('oculto');
    S.elMaster = $('#audioMaster');
    $('#audioOriginal').src = `/api/audio/${S.id}/original`;
    $('#nombreTema').textContent = d.nombre;
    S.medidasOriginal = d.medidas;
    $('#detalleTema').textContent = fmtSonando('Original', d.medidas.lufs, d.medidas.tp);
    ['#panelTema', '#panelOpciones'].forEach((s) => $(s).classList.remove('oculto'));

    const c = d.consejo || {};
    $('#perfilAudio').textContent = fmtPerfil(c.perfil);
    S.auto = c.auto || null;
    S.autoLufs = c.auto_lufs || {};
    S.presets = c.orden || [];
    S.sugerido = (S.presets[0] || {}).nombre || '';
    pintarPista();
    pintarOpciones();
    pintarOnda();
    cambiarAudio('original', false);
    aplicarAuto(null);
    masterizar('base_claro');        // todos los sistemas empiezan en Claro
  } finally {
    $('#barraSubida').classList.add('quieta');
  }
}

// ------------------------------------------------------------------ onda
// Onda de una versión concreta (la original o la masterizada que toque).
// Escala absoluta, como la app: 1,0 es el máximo reproducible, no se normaliza.
// Los picos los calcula el servidor: antes el panel se bajaba el WAV entero y lo
// decodificaba en la ventana, y ese pico de CPU era una de las causas de los tirones.
async function calcularPicos(cual) {
  try {
    const j = await (await fetch(`/api/picos/${S.id}/${cual}?v=${Date.now()}`)).json();
    return (j && j.picos) || null;
  } catch (e) {
    console.warn('no se pudo calcular la onda', e);
    return null;
  }
}

function picosDeLaVista() {
  return S.viendoOriginal
    ? (S.picosOriginal || S.picosMaster)
    : (S.picosMaster || S.picosOriginal);
}

// la gráfica que se ve siempre es la de la versión que está sonando
function pintarOndaDeLaVersion(progreso) {
  const picos = picosDeLaVista();
  if (picos) dibujarOnda(picos, progreso || 0);
}

async function pintarOnda() {
  const picos = await calcularPicos('original');
  if (!picos) return;
  S.picosOriginal = picos;
  pintarOndaDeLaVersion(0);
}

// Onda con caché: la base de barras se dibuja UNA vez en un lienzo aparte y en cada
// avance solo se repinta la parte ya escuchada. Antes se rehacía entera en cada
// «timeupdate» (varias veces por segundo) y por eso iba a tirones.
let baseOnda = null;
let claveBase = '';

function pintarBarras(ctx, picos, ancho, alto, progreso, color, soloHechas) {
  const paso = ancho / picos.length;
  const grosor = Math.max(1.5, paso * 0.62);
  const medio = alto / 2;
  const escala = (medio - 6) / 1.25;          // el 1,0 va dibujado por dentro
  const hasta = soloHechas ? Math.floor(picos.length * progreso) : picos.length;
  ctx.fillStyle = color;
  for (let i = 0; i < hasta; i++) {
    const v = Math.max(0.01, Math.min(1.6, picos[i]));
    const altoBarra = Math.max(1, escala * v);
    const x = i * paso + (paso - grosor) / 2;
    if (ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(x, medio - altoBarra, grosor, altoBarra * 2, grosor / 2);
      ctx.fill();
    } else {
      ctx.fillRect(x, medio - altoBarra, grosor, altoBarra * 2);
    }
  }
}

function dibujarOnda(picos, progreso) {
  const lienzo = $('#onda');
  if (!lienzo || !picos) return;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const ancho = Math.max(1, lienzo.clientWidth);
  const alto = Math.max(1, lienzo.clientHeight);
  const anchoReal = Math.round(ancho * dpr);
  const altoReal = Math.round(alto * dpr);
  if (lienzo.width !== anchoReal || lienzo.height !== altoReal) {
    lienzo.width = anchoReal;
    lienzo.height = altoReal;
    claveBase = '';
  }
  const clave = [S.viendoOriginal ? 'o' : 'm', picos.length, ancho, alto, dpr,
                 Math.round((picos[7] || 0) * 1000)].join('|');
  if (!baseOnda || clave !== claveBase) {
    baseOnda = document.createElement('canvas');
    baseOnda.width = anchoReal;
    baseOnda.height = altoReal;
    const b = baseOnda.getContext('2d');
    b.setTransform(dpr, 0, 0, dpr, 0, 0);
    b.strokeStyle = 'rgba(255,255,255,0.08)';
    b.lineWidth = 1;
    b.beginPath();
    b.moveTo(0, alto / 2);
    b.lineTo(ancho, alto / 2);
    b.stroke();
    pintarBarras(b, picos, ancho, alto, 0, 'rgba(255,255,255,0.20)', false);
    claveBase = clave;
  }
  const ctx = lienzo.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, anchoReal, altoReal);
  ctx.drawImage(baseOnda, 0, 0);
  if (progreso > 0) {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    pintarBarras(ctx, picos, ancho, alto, progreso, '#e30b5d', true);
  }
}

// ------------------------------------------------------------------ comparar
function pintarSonando() {
  if (!S.medidasOriginal) return;
  const linea = S.viendoOriginal
    ? fmtSonando('Original', S.medidasOriginal.lufs, S.medidasOriginal.tp)
    : fmtSonando(S.presetSonando || S.presetNombre || 'Masterizado',
        (S.medidasMaster || {}).lufs, (S.medidasMaster || {}).tp);
  $('#detalleTema').textContent = linea;
}

const REPRODUCTORES = ['#audioOriginal', '#audioMaster', '#audioMaster2'];

// ------------------------------------------------------------------ sonido
// El panel no usa los reproductores del navegador cuando el servidor puede sacar
// sonido: hay UNA tarjeta abierta y UNA posición compartida por todas las versiones,
// así que cambiar de ajuste es cambiar de dónde se leen las muestras. No hay parón,
// no hay salto de posición, no suenan dos a la vez y el navegador no puede bloquear
// el arranque automático (no pasa por él). Si no hay portaudio ni tarjeta, `nativo`
// se queda en falso y se usan los <audio> de siempre.
const REPRO = {
  nativo: false, clave: 'original', pos: 0, dur: 0, sonando: false,
  async init() {
    try {
      const j = await (await fetch('/api/repro/estado')).json();
      REPRO.nativo = j && j.disponible === true;
      REPRO.leer(j);
    } catch (e) {
      REPRO.nativo = false;
    }
    return REPRO.nativo;
  },
  leer(j) {
    if (!j) return;
    if (typeof j.pos === 'number') REPRO.pos = j.pos;
    if (typeof j.dur === 'number') REPRO.dur = j.dur;
    if (typeof j.sonando === 'boolean') REPRO.sonando = j.sonando;
    if (j.clave) REPRO.clave = String(j.clave).slice(-14);
  },
  async mando(accion, extra) {
    const cuerpo = Object.assign({ accion }, extra || {});
    if (S.id) cuerpo.id = S.id;
    try {
      const r = await fetch('/api/repro/mando', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo),
      });
      const j = await r.json();
      if (j && j.disponible === false) REPRO.nativo = false;
      REPRO.leer(j);
      return j;
    } catch (e) {
      return null;
    }
  },
  poner(cual, desde) { return REPRO.mando('poner', { cual, desde: desde || 0, sonar: true }); },
  // sonar sin valor = sigue como estaba (si el usuario había pausado, sigue en pausa)
  cambiar(cual, sonar) { return REPRO.mando('cambiar', { cual, sonar: sonar }); },
  pausa() { return REPRO.mando('pausa'); },
  seguir() { return REPRO.mando('seguir'); },
  ir(t) { return REPRO.mando('ir', { t }); },
};

// la onda y el botón Escuchar/Parar avanzan con la posición del servidor
function latirSonido() {
  if (!S.nativo || !S.id) return;
  fetch(`/api/repro/estado?id=${S.id}`).then((r) => r.json()).then((j) => {
    REPRO.leer(j);
    if (REPRO.dur > 0 && !S.arrastrando) {
      pintarOndaDeLaVersion(Math.min(1, REPRO.pos / REPRO.dur));
    }
  }).catch(() => {});
}

// Los navegadores pueden bloquear el sonido automático hasta que el usuario toca
// algo. Si pasa, se guarda y se reintenta en el primer clic o tecla.
// Todos los navegadores dejan arrancar en SILENCIO aunque bloqueen el sonido
// automático; en cuanto arranca se sube el volumen. Así suena solo en cualquier
// equipo, sin depender de opciones de arranque ni de que el usuario toque nada.
function arrancar(el) {
  if (!el) return;
  el.classList.remove('oculto');      // un reproductor con display:none no suena nunca
  if (!el.paused) {
    el.muted = false;
    S.pendienteSuena = null;
    return;
  }
  el.muted = true;
  let intento = null;
  try {
    intento = el.play();
  } catch (e) {
    el.muted = false;
    S.pendienteSuena = el;
    return;
  }
  if (intento && intento.then) {
    intento.then(() => { el.muted = false; S.pendienteSuena = null; })
           .catch((e) => { el.muted = false; S.pendienteSuena = el; S.ultimoError = (e && e.name) + ': ' + (e && e.message); });
  } else {
    el.muted = false;
  }
}

// (sin reintento al tocar en cualquier parte: daba arranques raros; solo suena al
// cargar, al cambiar de versión o al pulsar Escuchar)

function masterEnUso() {
  return S.elMaster || $('#audioMaster');
}

function audioActivo() {
  return S.viendoOriginal ? $('#audioOriginal') : masterEnUso();
}

// Cambia de un reproductor a otro en caliente: el que suena NO se toca hasta que el
// entrante está de verdad sonando. En ese instante se corrige la deriva (cargar el
// archivo puede retrasar el arranque unas centésimas) y solo entonces se para el
// saliente. Ni silencio ni dos versiones a la vez, y el corte cae en la misma posición.
function relevarEnCaliente(parar, entrante, visible, alinear) {
  const estado = { hecho: false, rescate: null };
  // rastro corto para poder mirar por qué no ha sonado en un equipo ajeno
  const nota = (txt) => {
    S.depuracion = S.depuracion || [];
    S.depuracion.push(txt + ' ' + Math.round(performance.now()));
    if (S.depuracion.length > 40) S.depuracion.shift();
  };
  const cerrar = (ok) => {
    if (estado.hecho) return;
    estado.hecho = true;
    clearTimeout(estado.rescate);
    if (!ok) {
      // no arrancó: sigue sonando el de antes y este queda apuntado para después
      nota('no arranca ' + entrante.id);
      S.pendienteSuena = entrante;
      if (!visible) entrante.classList.add('oculto');
      return;
    }
    nota('relevo ' + (parar ? parar.id : '-') + '→' + entrante.id);
    if (parar && parar !== entrante) {
      if (!parar.paused) {
        if (alinear !== false) {
          const deriva = parar.currentTime - entrante.currentTime;
          if (Math.abs(deriva) > 0.03) {
            try {
              entrante.currentTime = Math.max(0, entrante.currentTime + deriva);
            } catch (e) { /* sin datos todavía */ }
          }
        }
        parar.pause();
      }
      parar.classList.add('oculto');
    }
    // el que suena nunca puede quedarse con `oculto`: es display:none y WebKit lo para
    entrante.classList.remove('oculto');
    pintarSonando();
  };
  // Los navegadores bloquean el sonido automático hasta que hay un gesto del usuario,
  // pero SÍ dejan arrancar EN SILENCIO: si el primer intento es rechazado se reintenta
  // sin volumen y se sube en cuanto suena. Sin esto, al abrir con una canción cargada
  // o al llegar el primer ajuste no sonaba nada hasta pulsar un botón.
  const intenta = (silencioso) => {
    nota('play ' + entrante.id + (silencioso ? ' (mudo)' : ''));
    entrante.muted = silencioso;
    let intento = null;
    try {
      intento = entrante.play();
    } catch (e) {
      nota('excepción ' + e.name);
      if (!silencioso) { intenta(true); return; }
      cerrar(false);
      return;
    }
    if (intento && intento.then) {
      intento.then(() => { nota('play ok ' + entrante.id); if (!entrante.paused) cerrar(true); })
             .catch((e) => { nota('rechaza ' + (e && e.name)); if (!silencioso) intenta(true); else cerrar(false); });
    } else if (!entrante.paused) {
      cerrar(true);
    } else if (!silencioso) {
      intenta(true);
    }
  };
  // al primer `playing` se sube el volumen (si arrancó en silencio) y se releva el sonido
  entrante.addEventListener('playing', () => { entrante.muted = false; cerrar(true); }, { once: true });
  estado.rescate = setTimeout(() => { if (entrante.paused) cerrar(false); }, 1500);
  intenta(false);
  return estado;
}

// Coloca `entrante` en la posición pedida (o la de `parar`) y lo arranca con relevo.
function arrancarEnPosicion(entrante, parar, visible, posicion, alinear) {
  const arranca = () => {
    const donde = (posicion === undefined || posicion === null)
      ? (parar ? (parar.currentTime || 0) : 0) : posicion;
    try {
      entrante.currentTime = Math.min(donde, entrante.duration || donde);
    } catch (e) { /* sin datos todavía */ }
    relevarEnCaliente(parar, entrante, visible, alinear);
  };
  if (entrante.readyState >= 3) arranca();
  else entrante.addEventListener('canplay', arranca, { once: true });
}

function cambiarAudio(cual, conservar) {
  const aMaster = cual === 'master';
  S.viendoOriginal = !aMaster;
  document.querySelectorAll('#conmutador .opcion').forEach((b) => {
    b.classList.toggle('activa', b.dataset.cual === (S.viendoOriginal ? 'original' : 'master'));
  });
  if (S.nativo) {
    // la posición la lleva el servidor: al cambiar de versión sigue por donde iba,
    // sin parón y sin volver al principio (es lo que permite comparar A/B)
    if (conservar) REPRO.cambiar(cual); else REPRO.poner(cual, 0);
    pintarSonando();
    return;
  }
  const saliente = audioActivo();
  const entrante = aMaster ? masterEnUso() : $('#audioOriginal');
  if (!entrante.src) return;
  const sonaba = saliente && !saliente.paused;
  if (sonaba || !conservar) {
    if (conservar) arrancarEnPosicion(entrante, saliente, true, null, true);
    else arrancarEnPosicion(entrante, saliente, true, 0, false);
  } else {
    entrante.classList.remove('oculto');
    if (saliente && saliente !== entrante) {
      saliente.pause();
      saliente.classList.add('oculto');
    }
  }
  pintarSonando();
  pintarOndaDeLaVersion(entrante.duration ? entrante.currentTime / entrante.duration : 0);
}

// Como en la app: «Masterizado» no se puede pulsar hasta que su versión está lista
function marcarMasterListo(listo) {
  const boton = document.querySelector('#conmutador .opcion[data-cual="master"]');
  if (!boton) return;
  boton.disabled = !listo;
  boton.classList.toggle('esperando', !listo);
}

// Cambia la versión masterizada sin cortar lo que está sonando: el archivo nuevo
// se carga en el reproductor que NO suena y solo se cambia cuando ya puede
// reproducirse, en la misma posición. Si sonaba el original, se pasa al master.
// Si el relevo no llegó a arrancar (política del navegador o carga lenta), se
// reintenta una vez sobre el reproductor que debe estar sonando.
function asegurarSonando(espera) {
  setTimeout(() => {
    const el = masterEnUso();
    if (el && el.src && el.paused && !S.viendoOriginal) arrancar(el);
  }, espera === undefined ? 700 : espera);
}

function refrescarMaster(forzar) {
  const viejo = masterEnUso();
  const original = $('#audioOriginal');
  const nuevo = viejo.id === 'audioMaster' ? $('#audioMaster2') : $('#audioMaster');
  const sonandoOriginal = !original.paused;
  const sonando = forzar || sonandoOriginal || (!S.viendoOriginal && !viejo.paused);
  nuevo.src = `/api/audio/${S.id}/master?v=${Date.now()}`;
  const arranca = () => {
    // la posición se toma AHORA, no cuando se pidió el cambio: cargar el archivo puede
    // tardar y con la de antes se repetiría el trozo ya escuchado
    const fuente = (sonandoOriginal && !original.paused) ? original : viejo;
    const donde = fuente ? (fuente.currentTime || 0) : 0;
    try {
      nuevo.currentTime = Math.min(donde, nuevo.duration || donde);
    } catch (e) { /* sin datos todavía */ }
    S.elMaster = nuevo;                     // desde aquí manda el reproductor nuevo
    if (!sonando) {
      viejo.pause();
      viejo.classList.add('oculto');
      if (!S.viendoOriginal) nuevo.classList.remove('oculto');
      pintarSonando();
      return;
    }
    relevarEnCaliente(sonandoOriginal ? original : viejo, nuevo, !S.viendoOriginal, true);
  };
  if (nuevo.readyState >= 3) arranca();
  else nuevo.addEventListener('canplay', arranca, { once: true });
}

//  ------------------------------------------------------------------ ajustes
function botonDe(o) {
  const b = document.createElement('button');
  b.className = 'boton-opcion tarjeta-opcion';
  b.dataset.clave = o.clave;
  b.innerHTML = `<span class="nombre-preset">${T(o.nombre)}</span>`;
  b.addEventListener('click', () => masterizar(o.clave));
  return b;
}

function pintarOpciones() {
  const destacados = $('#listaDestacados');
  const recom = $('#listaRecomendadas');
  const resto = $('#listaOpciones');
  destacados.innerHTML = '';
  recom.innerHTML = '';
  resto.innerHTML = '';
  const porClave = {};
  S.presets.forEach((o) => { porClave[o.clave] = o; });
  DESTACADOS.forEach((clave) => {
    const o = porClave[clave];
    if (o) destacados.appendChild(botonDe(o));
  });
  // NORMA: en «Recomendadas por tipo de audio» nunca salen los fijos (Claro y Retro)
  const candidatas = S.presets.filter((o) => !DESTACADOS.includes(o.clave));
  candidatas.slice(0, 2).forEach((o) => recom.appendChild(botonDe(o)));
  $('#cajaRecomendada').classList.remove('oculto');
  S.presets.forEach((o) => {
    if (DESTACADOS.includes(o.clave)) return;
    resto.appendChild(botonDe(o));
  });
  $('#btnVariaciones').textContent = `${T('Más variaciones')} (${resto.children.length}) ▾`;
  $('#btnVariaciones').onclick = () => {
    const oculto = resto.classList.contains('oculto');
    resto.classList.toggle('oculto', !oculto);
    $('#btnVariaciones').textContent = oculto
      ? `${T('Más variaciones')} ▴` : `${T('Más variaciones')} (${resto.children.length}) ▾`;
  };
  pintarIconos();
}

// giro mientras calcula y visto verde cuando ya está hecho (igual que la app)
function pintarIconos() {
  document.querySelectorAll('.tarjeta-opcion').forEach((b) => {
    const clave = b.dataset.clave;
    const quiere = S.calculando.has(clave) ? 'giro' : (S.hechos.has(clave) ? 'visto' : null);
    let icono = b.querySelector('.icono-preset');
    if (!quiere) {
      if (icono) icono.remove();
      return;
    }
    if (!icono) {
      icono = document.createElement('span');
      b.appendChild(icono);
    }
    // solo se toca si cambia: reasignar la clase reinicia la animación en WebKit
    const clase = 'icono-preset ' + quiere;
    if (icono.className !== clase) icono.className = clase;
  });
}

async function masterizar(preset) {
  if (!S.id) return;
  S.preset = preset;
  document.querySelectorAll('.tarjeta-opcion').forEach((b) => {
    b.classList.toggle('activa', b.dataset.clave === preset);
  });
  const nombre = (S.presets.find((o) => o.clave === preset) || {}).nombre || preset;
  S.presetNombre = nombre;
  if (S.autoActivo) aplicarAuto(preset);
  S.pidiendo = true;
  if (!S.hechos.has(preset)) S.calculando.add(preset);   // ya calculado: sin giro
  pintarIconos();
  marcarMasterListo(false);
  $('#estadoTrabajo').textContent = `${T('Aplicando ')}${T(nombre)}…`;
  const cuerpo = {
    id: S.id,
    preset,
    intensidad: S.intensidad / 100,
    lufs: S.lufs,
    techo: null,
    formato: 'wav',
    auto: S.autoActivo
  };
  const respuesta = await fetch('/api/masterizar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo)
  });
  let cacheado = false;
  try {
    cacheado = (await respuesta.json()).cache === true;
  } catch (e) { /* sin respuesta clara: se espera al sondeo */ }
  if (cacheado) {
    S.calculando.delete(preset);
    S.hechos.add(preset);     // ya estaba calculado: el visto sale al momento
    pintarIconos();
    await consultar();
  }
}

// sondear el estado siempre: así los vistos van apareciendo según se calculan
async function consultar() {
  if (!S.id) return;
  const r = await fetch(`/api/estado/${S.id}`);
  if (!r.ok) {
    // el servicio se reinició y el trabajo ya no existe: se para, no se relanza solo
    S.id = null;
    S.pidiendo = false;
    S.calculando = new Set();
    pintarIconos();
    $('#estadoTrabajo').textContent = T('Se cortó: el servicio se reinició. Vuelve a elegir la canción.');
    return;
  }
  const j = await r.json();
  S.calculando = new Set(j.calculando || []);
  // el ajuste que acaba de pulsar el usuario no se cae del giro en la primera vuelta
  // (el servidor tarda unos milisegundos en marcarlo): si no, el icono parpadea
  if (S.pidiendo && S.preset && !S.hechos.has(S.preset)) S.calculando.add(S.preset);
  S.pendientes = j.pendientes || 0;
  // se SUMAN los hechos: lo ya calculado conserva su visto aunque el servidor
  // empiece otra tanda (antes se reemplazaba y los vistos desaparecían)
  (j.hechos || []).forEach((clave) => S.hechos.add(clave));
  pintarIconos();
  if (j.estado === 'listo') {
    marcarMasterListo(true);
    // solo se aplica si el ajuste terminado es el que se ha pedido: si no, una
    // respuesta vieja ('listo' del ajuste anterior) se comía el primer toque
    if (S.pidiendo && j.preset === S.preset) {
      const nombre = (S.presets.find((o) => o.clave === j.preset) || {}).nombre || j.preset;
      S.presetNombre = nombre;
      S.medidasMaster = j.medidas_master;
      S.pidiendo = false;
      $('#estadoTrabajo').textContent = '';
      $('#btnDescargar').href = `/api/descargar/${S.id}`;
      S.presetSonando = nombre;
      // como la app: al estar lista la versión se pasa sola a «Masterizado» y suena
      S.viendoOriginal = false;
      marcarMasterListo(true);
      document.querySelectorAll('#conmutador .opcion').forEach((b) => {
        b.classList.toggle('activa', b.dataset.cual === 'master');
      });
      pintarSonando();
      if (S.nativo) {
        // entra en la posición exacta en la que va el original, sin cortar el sonido
        REPRO.cambiar('master');
      } else {
        refrescarMaster(true);        // suena el ajuste en cuanto está listo
        asegurarSonando();
      }
      // la onda del ajuste nuevo se calcula aparte: la original y cada versión se ven distintas
      calcularPicos('master').then((picos) => {
        if (!picos) return;
        S.picosMaster = picos;
        if (!S.viendoOriginal) pintarOndaDeLaVersion(0);
      });
    }
  } else if (j.estado === 'error') {
    if (S.pidiendo) {
      S.pidiendo = false;
      $('#estadoTrabajo').textContent = T('Fallo: ') + (j.error || '');
    }
  } else if (S.pidiendo) {
    $('#estadoTrabajo').textContent = `${T('Aplicando ')}${T(S.presetNombre || '')}…`;
  }
}

// ------------------------------------------------------------------ finos
function ponerLufs(valor, manual) {
  const numero = Number(valor);
  if (!isFinite(numero)) return;
  const v = Math.max(-24, Math.min(-6, Number(numero.toFixed(1))));
  // Con Auto cada ajuste se calcula con SU sonoridad, así que cambiar de ajuste no
  // invalida los vistos de los demás: solo se limpian si el usuario mueve la barra
  // a mano. Limpiarlos al cambiar de ajuste hacía parpadear todos los iconos.
  if (v !== S.lufs && (manual || !S.autoActivo)) {
    S.hechos = new Set();      // otra sonoridad, otra tanda: los vistos ya no valen
    S.calculando = new Set();
    pintarIconos();
  }
  S.lufs = v;
  $('#lufs').value = v.toFixed(1);
  $('#barraLufs').value = v;
}

function ponerIntensidad(valor) {
  const v = Math.max(0, Math.min(120, Math.round(Number(valor) || 0)));
  if (v !== S.intensidad) {
    S.hechos = new Set();      // otra intensidad, otra tanda: los vistos ya no valen
    S.calculando = new Set();
    pintarIconos();
  }
  S.intensidad = v;
  $('#campoIntensidad').value = v;
  $('#barraIntensidad').value = v;
  $('#etiquetaIntensidad').textContent = `${T('Intensidad del efecto: ')}${v} %`;
}

function bloquear(sel, activo) {
  const el = $(sel);
  if (el) el.classList.toggle('bloqueado', !!activo);
}

// Auto: la sonoridad de cada ajuste la pone el análisis, no el usuario
function aplicarAuto(clave) {
  if (!S.autoActivo) return;
  const c = clave || S.preset || (S.presets[0] || {}).clave;
  let valor = S.autoLufs[c];
  if (valor === undefined || valor === null) valor = S.auto ? S.auto.lufs : null;
  if (valor !== null && valor !== undefined) ponerLufs(Number(valor));
}

let esperaCambio = null;
function pedirOtro() {
  clearTimeout(esperaCambio);
  esperaCambio = setTimeout(() => { if (S.preset) masterizar(S.preset); }, 700);
}

// Al abrir o recargar la página se recupera la última canción, como hace la app
async function iniciar() {
  // ¿puede el servidor sacar sonido por su cuenta? Es el camino bueno: sin parones
  // al cambiar de ajuste y sin que el navegador bloquee el arranque automático.
  S.nativo = await REPRO.init();
  AVISAR({ tipo: 'arranque', version: '1.0', tieneSesion: !!S.id, sonidoPropio: S.nativo,
           idioma: IDIOMA.valor, navegador: navigator.language });
  // banderas del idioma: cambian los textos sin tocar el sonido
  ['#btnIdiomaEs', '#btnIdiomaEn'].forEach((sel) => {
    const b = $(sel);
    if (b) b.addEventListener('click', () => {
      if (b.dataset.idioma === IDIOMA.valor) return;
      IDIOMA.poner(b.dataset.idioma);
      aplicarIdioma();
    });
  });
  pintarBanderas();
  const zona = $('#zonaSubida');
  const input = $('#archivo');
  zona.addEventListener('click', (ev) => {
    if (ev.target.id === 'archivo') return;
    input.click();
  });
  input.addEventListener('change', () => { if (input.files[0]) subir(input.files[0]); });

  // Arrastrar y soltar en toda la ventana: al soltar un archivo se carga, esté donde
  // esté el puntero. Así funciona igual en Chrome/Edge (Windows) y en WebKit (Linux).
  document.addEventListener('dragenter', (ev) => {
    ev.preventDefault();
    if (zona) zona.classList.add('encima');
  });
  document.addEventListener('dragover', (ev) => {
    ev.preventDefault();
    if (ev.dataTransfer) ev.dataTransfer.dropEffect = 'copy';
    if (zona) zona.classList.add('encima');
  });
  document.addEventListener('dragleave', (ev) => {
    if (!ev.relatedTarget && zona) zona.classList.remove('encima');
  });
  document.addEventListener('drop', (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    if (zona) zona.classList.remove('encima');
    const lista = ev.dataTransfer && ev.dataTransfer.files;
    if (!lista || !lista.length) return;
    const archivo = lista[0];
    if (archivo.size === 0) return;          // carpetas y accesos sin contenido
    subir(archivo);
  });

  document.querySelectorAll('#conmutador .opcion').forEach((b) => {
    b.addEventListener('click', () => { if (S.id) cambiarAudio(b.dataset.cual, true); });
  });

  // la onda se puede tocar para saltar, igual que en la app
  $('#onda').addEventListener('click', (ev) => {
    const caja = ev.currentTarget.getBoundingClientRect();
    const f = Math.max(0, Math.min(1, (ev.clientX - caja.left) / caja.width));
    if (S.nativo) {
      if (REPRO.dur > 0) REPRO.ir(f * REPRO.dur);
      pintarOndaDeLaVersion(f);
      return;
    }
    const el = audioActivo();
    if (!el || !el.duration) return;
    el.currentTime = f * el.duration;
    pintarOndaDeLaVersion(f);
  });

  const boton = $('#btnEscuchar');
  boton.addEventListener('click', () => {
    if (S.nativo) {
      if (REPRO.sonando) REPRO.pausa(); else REPRO.seguir();
      return;
    }
    const el = audioActivo();
    if (!el || !el.src) return;
    if (el.paused) { el.play().catch(() => {}); } else { el.pause(); }
  });
  setInterval(() => {
    const suena = S.nativo ? REPRO.sonando
      : (() => { const el = audioActivo(); return !!(el && el.src && !el.paused); })();
    const texto = T(suena ? '■ Parar' : '▶ Escuchar');
    if (boton.textContent !== texto) boton.textContent = texto;
  }, 400);
  // la posición la manda el servidor cuando el sonido es suyo
  setInterval(latirSonido, 250);

  $('#btnDescargar').addEventListener('click', (ev) => {
    if (!$('#btnDescargar').getAttribute('href') || $('#btnDescargar').getAttribute('href') === '#') {
      ev.preventDefault();
    }
  });

  REPRODUCTORES.forEach((sel) => {
    const el = $(sel);
    // el audio va en bucle: al llegar al final vuelve a empezar
    el.addEventListener('ended', () => {
      el.currentTime = 0;
      arrancar(el);
    });
    el.addEventListener('timeupdate', () => {
      if (el !== audioActivo() || !picosDeLaVista()) return;
      const ahora = performance.now();
      if (ahora - (S.ultimaOnda || 0) < 120) return;   // 8 repintados por segundo bastan
      S.ultimaOnda = ahora;
      pintarOndaDeLaVersion(el.currentTime / (el.duration || 1));
    });
    el.addEventListener('play', () => {
      REPRODUCTORES.forEach((otroSel) => {
        const otro = $(otroSel);
        if (otro !== el && !otro.paused) otro.pause();
      });
    });
  });

  // Auto arranca activado y bloquea sonoridad (como la app)
  $('#btnAuto').addEventListener('click', () => {
    S.autoActivo = !S.autoActivo;
    $('#btnAuto').textContent = T(S.autoActivo ? 'Auto ✓' : 'Auto');
    $('#btnAuto').classList.toggle('activo', S.autoActivo);
    bloquear('#barraLufs', S.autoActivo);
    bloquear('#lufs', S.autoActivo);
    if (S.autoActivo) {
      aplicarAuto(S.preset);
      if (S.preset) masterizar(S.preset);
    }
  });

  // Fijo arranca activado y bloquea la intensidad (como la app)
  $('#btnFijo').addEventListener('click', () => {
    S.fijoActivo = !S.fijoActivo;
    $('#btnFijo').textContent = T(S.fijoActivo ? 'Fijo ✓' : 'Fijo');
    $('#btnFijo').classList.toggle('activo', S.fijoActivo);
    bloquear('#barraIntensidad', S.fijoActivo);
    bloquear('#campoIntensidad', S.fijoActivo);
  });

  $('#barraLufs').addEventListener('input', (ev) => {
    if (S.autoActivo) return;
    ponerLufs(ev.target.value, true);
    pedirOtro();
  });
  $('#lufs').addEventListener('input', (ev) => {
    if (S.autoActivo || ev.target.value === '') return;
    ponerLufs(ev.target.value, true);
    pedirOtro();
  });
  $('#barraIntensidad').addEventListener('input', (ev) => {
    if (S.fijoActivo) return;
    ponerIntensidad(ev.target.value);
    pedirOtro();
  });
  $('#campoIntensidad').addEventListener('input', (ev) => {
    if (S.fijoActivo || ev.target.value === '') return;
    ponerIntensidad(ev.target.value);
    pedirOtro();
  });

  const finos = $('#detalleFinos');
  const resumen = $('#resumenFinos');
  finos.addEventListener('toggle', () => {
    resumen.textContent = T(finos.open ? 'Ajustes finos ▾' : 'Ajustes finos ▸');
  });

  // estado inicial igual que la app
  S.elMaster = $('#audioMaster');
  marcarMasterListo(false);
  ponerLufs(-10);
  ponerIntensidad(100);
  $('#btnAuto').classList.add('activo');
  $('#btnFijo').classList.add('activo');
  bloquear('#barraLufs', true);
  bloquear('#lufs', true);
  bloquear('#barraIntensidad', true);
  bloquear('#campoIntensidad', true);
  dibujarOnda(new Array(220).fill(0.06), 0);
  mirarMotores();
  aplicarIdioma();          // la primera vez, el idioma detectado del sistema
  arrancarEnLimpio();       // al abrir NO se retoma la última canción
  // el estado se mira cada 1,2 s, pero mientras hay ajustes en marcha cada 400 ms:
// así el giro se convierte en visto en cuanto termina, sin retraso apreciable
let relojEstado = 0;
function latirEstado() {
  const trabajando = S.pidiendo || (S.calculando && S.calculando.size > 0) || (S.pendientes || 0) > 0;
  if (trabajando) S.ultimoTrabajo = Date.now();
  // rápido mientras haya cola detrás y 1,5 s más después: el último visto entra sin espera
  const prisa = trabajando || (Date.now() - (S.ultimoTrabajo || 0) < 1500);
  const espera = prisa ? 250 : 1200;
  clearTimeout(relojEstado);
  relojEstado = setTimeout(async () => {
    try {
      await consultar();
    } finally {
      latirEstado();
    }
  }, espera);
}
latirEstado();
}

/* Los enlaces que salen del panel (Donar, iaradio.es…) los abre el servidor en el
   navegador del sistema. Dentro de la ventana GTK+WebKit y de WebView2 se perdían:
   no hay pestañas y las ventanas nuevas se descartan. */
document.addEventListener('click', (ev) => {
  const enlace = ev.target.closest && ev.target.closest('a[data-fuera], a[href^="http"]');
  if (!enlace) return;
  const destino = enlace.getAttribute('href');
  if (!destino || !destino.startsWith('http')) return;
  const mismoSitio = destino.includes(location.host);
  if (mismoSitio) return;
  ev.preventDefault();
  fetch('/api/abrir', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: destino })
  }).catch(() => { window.open(destino, '_blank'); });
});

iniciar();
