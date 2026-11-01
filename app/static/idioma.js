'use strict';

const TRAD = {
  
  'Remasterizado de Audio por Ecualización': 'Audio Remastering by Equalization',
  'Elegir audio': 'Choose audio',
  '***No se recomienda subir audio ya remasterizado***':
    '***Uploading already-remastered audio is not recommended***',
  'Ningún audio elegido': 'No audio selected',
  'Qué se ha analizado': 'What has been analyzed',
  'Sube una canción para verlo': 'Load a song to see it',
  'Comparar': 'Compare',
  'Original': 'Original',
  'Masterizado': 'Mastered',
  '▶ Escuchar': '▶ Listen',
  '■ Parar': '■ Stop',
  'Descargar': 'Download',
  '♥ Donar': '♥ Donate',
  'Habituales': 'Essentials',
  'Empiezas con Amplificador. Toca otro para cambiarlo.':
    'You start with Amplifier. Tap another one to change it.',
  'Recomendadas por tipo de audio': 'Recommended by audio type',
  'Ajustes finos ▸': 'Fine tuning ▸',
  'Ajustes finos ▾': 'Fine tuning ▾',
  'Sonoridad (LUFS)': 'Loudness (LUFS)',
  'Auto ✓': 'Auto ✓',
  'Auto': 'Auto',
  'Fijo ✓': 'Fixed ✓',
  'Fijo': 'Fixed',
  'Optimizando Rendimiento': 'Optimizing performance',

  
  'Analizando…': 'Analyzing…',
  'Trabajando…': 'Working…',
  'Aplicando ': 'Applying ',
  'Intensidad del efecto: ': 'Effect intensity: ',
  'Más variaciones': 'More variations',
  'pico': 'peak',
  'audio largo': 'long audio',
  'graves': 'bass',
  'agudos': 'treble',
  'Motor principal: ': 'Main engine: ',
  'Motor secundario: ': 'Secondary engine: ',
  'Empiezas con Claro; cámbialo cuando quieras.':
    'You start with Clear; change it whenever you like.',
  'Por cómo suena, encaja ': 'By how it sounds, ',
  '. Empiezas con Claro; cámbialo cuando quieras.':
    ' fits best. You start with Clear; change it whenever you like.',
  'Se cortó: el servicio se reinició. Vuelve a elegir la canción.':
    'It stopped: the service restarted. Choose the song again.',
  'Fallo: ': 'Failed: ',
  'El servidor no ha entendido el archivo (¿está dañado?)':
    'The server could not read the file (is it damaged?)',
  'No se ha podido leer el audio': 'The audio could not be read',
  'No ha llegado ningún archivo': 'No file arrived',
  'No se ha podido leer el audio (¿formato no soportado?)':
    'The audio could not be read (unsupported format?)',
  'Ese audio está en silencio (o no se oye nada)':
    'That audio is silent (nothing can be heard)',
  'sin sonido propio': 'no built-in sound',
  'sonido propio': 'built-in sound',

  
  'Amplificador': 'Amplifier',
  'Caliente': 'Hot',
  'Claro': 'Clear',
  'Retro': 'Retro',
  'Neutra': 'Neutral',
  'Amplia': 'Wide',
  'Film': 'Film',
  'Potente': 'Powerful',
  'Audiolibro': 'Audiobook',
  'Podcast': 'Podcast',
  'Aire': 'Air',
  'Luminosa': 'Luminous',
  'Sencilla': 'Simple',
  'Suave': 'Soft',
  'Terciopelo': 'Velvet',
  'Chispa': 'Spark',
  'Viva': 'Vivid',
  'Habitual': 'Regular',
  'Cálida': 'Warm',
  'Sedosa': 'Silky',
  'Deslumbrante': 'Dazzling',
  'Radiante': 'Radiant',
  'Firme': 'Firm',
  'Densa': 'Dense',
  'Oscura': 'Dark'
};

const INVERSO = {};
Object.keys(TRAD).forEach((es) => { INVERSO[TRAD[es]] = es; });

const IDIOMA = {
  clave: 'pitmasteraudio.idioma',
  valor: 'es',

  
  inicio() {
    let guardado = null;
    try {
      guardado = localStorage.getItem(this.clave);
    } catch (e) {  }
    if (guardado === 'es' || guardado === 'en') {
      this.valor = guardado;
      return this.valor;
    }
    const nav = String(navigator.language || navigator.userLanguage || 'es').toLowerCase();
    this.valor = nav.indexOf('es') === 0 ? 'es' : 'en';
    this.guardar();
    return this.valor;
  },

  guardar() {
    try {
      localStorage.setItem(this.clave, this.valor);
    } catch (e) {  }
  },

  poner(cual) {
    this.valor = cual === 'en' ? 'en' : 'es';
    this.guardar();
  },

  
  t(texto) {
    if (texto === null || texto === undefined) return texto;
    if (this.valor === 'en') {
      return Object.prototype.hasOwnProperty.call(TRAD, texto) ? TRAD[texto] : texto;
    }
    return Object.prototype.hasOwnProperty.call(INVERSO, texto) ? INVERSO[texto] : texto;
  }
};

IDIOMA.inicio();

function T(texto) {
  return IDIOMA.t(texto);
}
