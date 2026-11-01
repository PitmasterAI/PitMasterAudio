# PitMasterAudio — motor de audio y panel (Linux)

Documento para quien toque el motor Python y el panel web. Los números están medidos
en este equipo (ROG Ally: APU AMD RADV PHOENIX, 8 núcleos físicos, 8 GB) y en pop-os
(pc@192.168.1.144: 12 núcleos físicos, 62 GB, RTX 3090).

## 1. Piezas

| Fichero | Qué hace |
|---|---|
| `motor.py` | Cadena completa de masterizado (`chain`), lectura/escritura y modo consola. |
| `dsp.py` | El DSP: EQ, compresión multibanda, saturación, estéreo, reverb, limitador, pico real, LUFS. |
| `gpuops.py` | Capa de GPU: Vulkan primero, torch/CUDA después, numpy si no hay nada. |
| `vk_compute.py` | Vulkan por ctypes: instancia, dispositivo, buffers y envío de los shaders. |
| `vk/*.comp`, `vk/*.spv` | Shaders GLSL y su SPIR-V compilado (`glslc --target-env=vulkan1.1 -O`). |
| `paralelo.py` | Cuántas instancias de cada motor aguanta el equipo (prueba + guardado). |
| `aceleracion.py` | Qué motor es el principal y cuál el secundario; se guarda en `~/.masterlab_motor.json`. |
| `bench_paralelo.py` | Banco: tiempo de N ajustes con 1..K trabajadores, en CPU, GPU o híbrido. |
| `app/app.py` | Panel Flask: subida, análisis, precálculo, masterizado, descargas. |
| `app/analiza.py` | Análisis y nombres/descripciones de los ajustes. |

## 2. La cadena (`motor.chain`)

Pasa-altos → EQ (curva de 29 bandas compensada por `compensate`) → compresión en tres
bandas (corte 250/3000 Hz) → saturación → ancho estéreo → reverb → sonoridad objetivo
con limitador. La sonoridad se clava **iterando** desde `app.py` (hasta 3 pasadas,
tolerancia 0,08 LU) porque si el techo no deja llegar al objetivo hay que volver a
limitar con más ganancia.

`dsp.py` usa GPU cuando `gpuops` tiene backend: saturación, estéreo, pico real y las 4
fases polifásicas de la envolvente true-peak. Los filtros con memoria (one-pole,
biquad) se quedan en CPU a propósito: en GPU salen más lentos.

## 3. Vulkan por ctypes (`vk_compute.py`)

- **Todas** las funciones de Vulkan necesitan `argtypes` declarados: sin ellos ctypes
  recorta los punteros a 32 bits y el proceso muere con violación de segmento.
- El SPIR-V va como `uint32_t[]` (alineado a 4 bytes).
- Se guarda `tipo` (VkPhysicalDeviceType: 1 integrada, 2 dedicada) leído de
  `VkPhysicalDeviceProperties`; lo usa `paralelo.py`.
- **No es seguro entre hilos**: varias instancias simultáneas pueden tumbar el proceso
  (con el iGPU AMD del Ally pasa siempre a partir de 2; en la 3090 el fallo es
  intermitente a partir de 4-8). Por eso cada prueba va en un subproceso.

## 4. Cuántas instancias por motor (`paralelo.py`)

Regla fija, la misma que la app de Android (motor principal y motor secundario):

- **CPU**: **1** trabajador de precálculo, en cualquier aparato.
- **GPU**: **1** trabajador si hay tarjeta (integrada o dedicada); **0** si no la hay,
  y entonces todo va por el único hilo de CPU.
- No hay banco de pruebas ni configuración guardada que consultar: `en_vivo()` mira si
  hay Vulkan y devuelve `{cpu: 1, gpu: 1|0}`. `~/.masterlab_paralelo.json` se escribe
  solo como referencia del equipo.
- El panel lanza un hilo de precálculo por motor (la cola está bajo `COLA_LOCK`). La
  GPU sigue protegida por el cerrojo de `vk_compute` y los turnos por memoria libre
  (`_entrar_calculo`) siguen limitando cuántas cadenas corren a la vez.
- `/api/optimizando` existe por compatibilidad y siempre responde `activo: false`: ya no
  hay prueba que enseñar.

## 5. Panel (`app/app.py`)

- `JOBS[sid]` guarda el estado de cada tema; `FUENTES` cachea el audio decodificado en
  RAM; `COLA_LOCK` protege la cola compartida de precálculo.
- El precálculo lanza N hilos por motor y cada uno coge el siguiente ajuste de la cola.
- El hilo del usuario va por el motor **principal** (`_motor_hilo('GPU')`), el
  precálculo por el secundario (`gpuops.fijar('CPU')`).
- Endpoints: `/api/subir`, `/api/masterizar`, `/api/estado/<sid>`, `/api/presets`,
  `/api/optimizando`, `/api/descargar/<sid>?formato=wav|mp3`.
- Siempre se generan WAV 24 bits y MP3 320 kbps con FFmpeg.

## 6. Números medidos (28-10, audio de 60 s)

**Una canción con todos los ajustes (23 ajustes musicales):**

| Equipo | Configuración | Tiempo total | Por ajuste |
|---|---|---|---|
| ROG Ally | 1 instancia CPU | 157,05 s | 6,83 s |
| ROG Ally | tras la prueba: 2 CPU + 1 GPU | **70,84 s** | 3,08 s |
| pop-os | 1 instancia CPU | 138,36 s | 6,02 s |
| pop-os | tras la prueba: 12 CPU + 2 GPU | **39,71 s** | 1,73 s |

**Escalado con 8 ajustes (mismo audio):**

| Instancias | Ally CPU | Ally GPU | pop-os CPU | pop-os GPU |
|---|---|---|---|---|
| 1 | 38,47 s | 30,66 s | 34,73 s | 21,20 s |
| 2 | 25,65 s | falla (seg) | 18,28 s | 13,04 s |
| 4 | 16,25 s | — | 11,96 s | 14,48 s |
| 8 | 16,46 s | — | 9,00 s | 6,75 s |

**Conclusiones que sostienen la configuración**

- En el iGPU AMD del Ally solo vale **una** instancia de GPU; la segunda tumba el proceso.
- En la 3090 escalan varias instancias, pero el driver revienta de forma intermitente
  a partir de 4-8; de ahí la prueba con margen a la mitad.
- El híbrido GPU+CPU no supera a la GPU sola en pop-os (9,86 s frente a 6,75 s con 8) y
  en el Ally empata con CPU sola.
- Vulkan dobla la velocidad en PC (2,04× en el Ally, 2,34× en pop-os) pero en el móvil
  es más lento que la CPU.
