

__version__ = '0.5.3'

import atexit as _atexit
import os as _os
import platform as _platform
import sys as _sys
from ctypes.util import find_library as _find_library
from _sounddevice import ffi as _ffi

try:
    for _libname in (
            'portaudio',
            'bin\\libportaudio-2.dll',
            'lib/libportaudio.dylib',
            ):
        _libname = _find_library(_libname)
        if _libname is not None:
            break
    else:
        raise OSError('PortAudio library not found')
    _lib = _ffi.dlopen(_libname)
except OSError:
    if _platform.system() == 'Darwin':
        _libname = 'libportaudio.dylib'
    elif _platform.system() == 'Windows':
        if 'SD_ENABLE_ASIO' in _os.environ:
            _libname = 'libportaudio' + _platform.architecture()[0] + '-asio.dll'
        else:
            _libname = 'libportaudio' + _platform.architecture()[0] + '.dll'
    else:
        raise
    import _sounddevice_data
    _libname = _os.path.join(
        next(iter(_sounddevice_data.__path__)), 'portaudio-binaries', _libname)
    _lib = _ffi.dlopen(_libname)

_sampleformats = {
    'float32': _lib.paFloat32,
    'int32': _lib.paInt32,
    'int24': _lib.paInt24,
    'int16': _lib.paInt16,
    'int8': _lib.paInt8,
    'uint8': _lib.paUInt8,
}

_initialized = 0
_last_callback = None

def play(data, samplerate=None, mapping=None, blocking=False, loop=False,
         **kwargs):
    ctx = _CallbackContext(loop=loop)
    ctx.frames = ctx.check_data(data, mapping, kwargs.get('device'))

    def callback(outdata, frames, time, status):
        assert len(outdata) == frames
        ctx.callback_enter(status, outdata)
        ctx.write_outdata(outdata)
        ctx.callback_exit()

    ctx.start_stream(OutputStream, samplerate, ctx.output_channels,
                     ctx.output_dtype, callback, blocking,
                     prime_output_buffers_using_stream_callback=False,
                     **kwargs)

def rec(frames=None, samplerate=None, channels=None, dtype=None,
        out=None, mapping=None, blocking=False, **kwargs):
    ctx = _CallbackContext()
    out, ctx.frames = ctx.check_out(out, frames, channels, dtype, mapping)

    def callback(indata, frames, time, status):
        assert len(indata) == frames
        ctx.callback_enter(status, indata)
        ctx.read_indata(indata)
        ctx.callback_exit()

    ctx.start_stream(InputStream, samplerate, ctx.input_channels,
                     ctx.input_dtype, callback, blocking, **kwargs)
    return out

def playrec(data, samplerate=None, channels=None, dtype=None,
            out=None, input_mapping=None, output_mapping=None, blocking=False,
            **kwargs):
    ctx = _CallbackContext()
    output_frames = ctx.check_data(data, output_mapping, kwargs.get('device'))
    if dtype is None:
        dtype = ctx.data.dtype
    out, input_frames = ctx.check_out(out, output_frames, channels, dtype,
                                      input_mapping)
    if input_frames != output_frames:
        raise ValueError('len(data) != len(out)')
    ctx.frames = input_frames

    def callback(indata, outdata, frames, time, status):
        assert len(indata) == len(outdata) == frames
        ctx.callback_enter(status, indata)
        ctx.read_indata(indata)
        ctx.write_outdata(outdata)
        ctx.callback_exit()

    ctx.start_stream(Stream, samplerate,
                     (ctx.input_channels, ctx.output_channels),
                     (ctx.input_dtype, ctx.output_dtype),
                     callback, blocking,
                     prime_output_buffers_using_stream_callback=False,
                     **kwargs)
    return out

def wait(ignore_errors=True):
    if _last_callback:
        return _last_callback.wait(ignore_errors)

def stop(ignore_errors=True):
    if _last_callback:

        _last_callback.stream.stop(ignore_errors)
        _last_callback.stream.close(ignore_errors)

def get_status():
    if _last_callback:
        return _last_callback.status
    else:
        raise RuntimeError('play()/rec()/playrec() was not called yet')

def get_stream():
    if _last_callback:
        return _last_callback.stream
    else:
        raise RuntimeError('play()/rec()/playrec() was not called yet')

def query_devices(device=None, kind=None):
    if kind not in ('input', 'output', None):
        raise ValueError(f'Invalid kind: {kind!r}')
    if device is None and kind is None:
        return DeviceList(query_devices(i)
                          for i in range(_check(_lib.Pa_GetDeviceCount())))
    device = _get_device_id(device, kind, raise_on_error=True)
    info = _lib.Pa_GetDeviceInfo(device)
    if not info:
        raise PortAudioError(f'Error querying device {device}')
    assert info.structVersion == 2
    name_bytes = _ffi.string(info.name)
    try:

        name = name_bytes.decode('utf-8')
    except UnicodeDecodeError:
        api_idx = _lib.Pa_HostApiTypeIdToHostApiIndex
        if info.hostApi in (api_idx(_lib.paDirectSound), api_idx(_lib.paMME)):
            name = name_bytes.decode('mbcs')
        elif info.hostApi == api_idx(_lib.paASIO):

            import locale
            name = name_bytes.decode(locale.getpreferredencoding())
        else:
            raise
    device_dict = {
        'name': name,
        'index': device,
        'hostapi': info.hostApi,
        'max_input_channels': info.maxInputChannels,
        'max_output_channels': info.maxOutputChannels,
        'default_low_input_latency': info.defaultLowInputLatency,
        'default_low_output_latency': info.defaultLowOutputLatency,
        'default_high_input_latency': info.defaultHighInputLatency,
        'default_high_output_latency': info.defaultHighOutputLatency,
        'default_samplerate': info.defaultSampleRate,
    }
    if kind and device_dict['max_' + kind + '_channels'] < 1:
        raise ValueError(
            'Not an {} device: {!r}'.format(kind, device_dict['name']))
    return device_dict

def query_hostapis(index=None):
    if index is None:
        return tuple(query_hostapis(i)
                     for i in range(_check(_lib.Pa_GetHostApiCount())))
    info = _lib.Pa_GetHostApiInfo(index)
    if not info:
        raise PortAudioError(f'Error querying host API {index}')
    assert info.structVersion == 1
    return {
        'name': _ffi.string(info.name).decode(),
        'devices': [_lib.Pa_HostApiDeviceIndexToDeviceIndex(index, i)
                    for i in range(info.deviceCount)],
        'default_input_device': info.defaultInputDevice,
        'default_output_device': info.defaultOutputDevice,
    }

def check_input_settings(device=None, channels=None, dtype=None,
                         extra_settings=None, samplerate=None):
    parameters, dtype, samplesize, samplerate = _get_stream_parameters(
        'input', device=device, channels=channels, dtype=dtype, latency=None,
        extra_settings=extra_settings, samplerate=samplerate)
    _check(_lib.Pa_IsFormatSupported(parameters, _ffi.NULL, samplerate))

def check_output_settings(device=None, channels=None, dtype=None,
                          extra_settings=None, samplerate=None):
    parameters, dtype, samplesize, samplerate = _get_stream_parameters(
        'output', device=device, channels=channels, dtype=dtype, latency=None,
        extra_settings=extra_settings, samplerate=samplerate)
    _check(_lib.Pa_IsFormatSupported(_ffi.NULL, parameters, samplerate))

def sleep(msec):
    _lib.Pa_Sleep(msec)

def get_portaudio_version():
    return _lib.Pa_GetVersion(), _ffi.string(_lib.Pa_GetVersionText()).decode()

class _StreamBase:

    def __init__(self, kind, samplerate=None, blocksize=None, device=None,
                 channels=None, dtype=None, latency=None, extra_settings=None,
                 callback=None, finished_callback=None, clip_off=None,
                 dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None,
                 userdata=None, wrap_callback=None):
        assert kind in ('input', 'output', 'duplex')
        assert wrap_callback in ('array', 'buffer', None)
        if wrap_callback == 'array':

            import numpy
            assert numpy

        if blocksize is None:
            blocksize = default.blocksize
        if clip_off is None:
            clip_off = default.clip_off
        if dither_off is None:
            dither_off = default.dither_off
        if never_drop_input is None:
            never_drop_input = default.never_drop_input
        if prime_output_buffers_using_stream_callback is None:
            prime_output_buffers_using_stream_callback = \
                default.prime_output_buffers_using_stream_callback

        stream_flags = _lib.paNoFlag
        if clip_off:
            stream_flags |= _lib.paClipOff
        if dither_off:
            stream_flags |= _lib.paDitherOff
        if never_drop_input:
            stream_flags |= _lib.paNeverDropInput
        if prime_output_buffers_using_stream_callback:
            stream_flags |= _lib.paPrimeOutputBuffersUsingStreamCallback

        if kind == 'duplex':
            idevice, odevice = _split(device)
            ichannels, ochannels = _split(channels)
            idtype, odtype = _split(dtype)
            ilatency, olatency = _split(latency)
            iextra, oextra = _split(extra_settings)
            iparameters, idtype, isize, isamplerate = _get_stream_parameters(
                'input', idevice, ichannels, idtype, ilatency, iextra,
                samplerate)
            oparameters, odtype, osize, osamplerate = _get_stream_parameters(
                'output', odevice, ochannels, odtype, olatency, oextra,
                samplerate)
            self._dtype = idtype, odtype
            self._device = iparameters.device, oparameters.device
            self._channels = iparameters.channelCount, oparameters.channelCount
            self._samplesize = isize, osize
            if isamplerate != osamplerate:
                raise ValueError(
                    'Input and output device must have the same samplerate')
            else:
                samplerate = isamplerate
        else:
            parameters, self._dtype, self._samplesize, samplerate = \
                _get_stream_parameters(kind, device, channels, dtype, latency,
                                       extra_settings, samplerate)
            self._device = parameters.device
            self._channels = parameters.channelCount
            iparameters = _ffi.NULL
            oparameters = _ffi.NULL
            if kind == 'input':
                iparameters = parameters
            elif kind == 'output':
                oparameters = parameters

        ffi_callback = _ffi.callback('PaStreamCallback', error=_lib.paAbort)

        if callback is None:
            callback_ptr = _ffi.NULL
        elif kind == 'input' and wrap_callback == 'buffer':

            @ffi_callback
            def callback_ptr(iptr, optr, frames, time, status, _):
                data = _buffer(iptr, frames, self._channels, self._samplesize)
                return _wrap_callback(callback, data, frames, time, status)

        elif kind == 'input' and wrap_callback == 'array':

            @ffi_callback
            def callback_ptr(iptr, optr, frames, time, status, _):
                data = _array(
                    _buffer(iptr, frames, self._channels, self._samplesize),
                    self._channels, self._dtype)
                return _wrap_callback(callback, data, frames, time, status)

        elif kind == 'output' and wrap_callback == 'buffer':

            @ffi_callback
            def callback_ptr(iptr, optr, frames, time, status, _):
                data = _buffer(optr, frames, self._channels, self._samplesize)
                return _wrap_callback(callback, data, frames, time, status)

        elif kind == 'output' and wrap_callback == 'array':

            @ffi_callback
            def callback_ptr(iptr, optr, frames, time, status, _):
                data = _array(
                    _buffer(optr, frames, self._channels, self._samplesize),
                    self._channels, self._dtype)
                return _wrap_callback(callback, data, frames, time, status)

        elif kind == 'duplex' and wrap_callback == 'buffer':

            @ffi_callback
            def callback_ptr(iptr, optr, frames, time, status, _):
                ichannels, ochannels = self._channels
                isize, osize = self._samplesize
                idata = _buffer(iptr, frames, ichannels, isize)
                odata = _buffer(optr, frames, ochannels, osize)
                return _wrap_callback(
                    callback, idata, odata, frames, time, status)

        elif kind == 'duplex' and wrap_callback == 'array':

            @ffi_callback
            def callback_ptr(iptr, optr, frames, time, status, _):
                ichannels, ochannels = self._channels
                idtype, odtype = self._dtype
                isize, osize = self._samplesize
                idata = _array(_buffer(iptr, frames, ichannels, isize),
                               ichannels, idtype)
                odata = _array(_buffer(optr, frames, ochannels, osize),
                               ochannels, odtype)
                return _wrap_callback(
                    callback, idata, odata, frames, time, status)

        else:

            callback_ptr = _ffi.cast('PaStreamCallback*', callback)

        self._callback = callback_ptr
        if userdata is None:
            userdata = _ffi.NULL
        self._ptr = _ffi.new('PaStream**')
        _check(_lib.Pa_OpenStream(self._ptr, iparameters, oparameters,
                                  samplerate, blocksize, stream_flags,
                                  callback_ptr, userdata),
               f'Error opening {self.__class__.__name__}')

        self._ptr = self._ptr[0]

        self._blocksize = blocksize
        info = _lib.Pa_GetStreamInfo(self._ptr)
        if not info:
            raise PortAudioError('Could not obtain stream info')

        self._samplerate = info.sampleRate
        if not oparameters:
            self._latency = info.inputLatency
        elif not iparameters:
            self._latency = info.outputLatency
        else:
            self._latency = info.inputLatency, info.outputLatency

        if finished_callback:
            if isinstance(finished_callback, _ffi.CData):
                self._finished_callback = finished_callback
            else:

                def finished_callback_wrapper(_):
                    return finished_callback()

                self._finished_callback = _ffi.callback(
                    'PaStreamFinishedCallback', finished_callback_wrapper)
            _check(_lib.Pa_SetStreamFinishedCallback(self._ptr,
                                                     self._finished_callback))

    _ptr = _ffi.NULL

    @property
    def samplerate(self):
        return self._samplerate

    @property
    def blocksize(self):
        return self._blocksize

    @property
    def device(self):
        return self._device

    @property
    def channels(self):
        return self._channels

    @property
    def dtype(self):
        return self._dtype

    @property
    def samplesize(self):
        return self._samplesize

    @property
    def latency(self):
        return self._latency

    @property
    def active(self):
        if self.closed:
            return False
        return _check(_lib.Pa_IsStreamActive(self._ptr)) == 1

    @property
    def stopped(self):
        if self.closed:
            return True
        return _check(_lib.Pa_IsStreamStopped(self._ptr)) == 1

    @property
    def closed(self):
        return self._ptr == _ffi.NULL

    @property
    def time(self):
        time = _lib.Pa_GetStreamTime(self._ptr)
        if not time:
            raise PortAudioError('Error getting stream time')
        return time

    @property
    def cpu_load(self):
        return _lib.Pa_GetStreamCpuLoad(self._ptr)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
        self.close()

    def start(self):
        err = _lib.Pa_StartStream(self._ptr)
        if err != _lib.paStreamIsNotStopped:
            _check(err, 'Error starting stream')

    def stop(self, ignore_errors=True):
        err = _lib.Pa_StopStream(self._ptr)
        if not ignore_errors:
            _check(err, 'Error stopping stream')

    def abort(self, ignore_errors=True):
        err = _lib.Pa_AbortStream(self._ptr)
        if not ignore_errors:
            _check(err, 'Error aborting stream')

    def close(self, ignore_errors=True):
        err = _lib.Pa_CloseStream(self._ptr)
        self._ptr = _ffi.NULL
        if not ignore_errors:
            _check(err, 'Error closing stream')

class _InputStreamBase(_StreamBase):

    @property
    def read_available(self):
        return _check(_lib.Pa_GetStreamReadAvailable(self._ptr))

    def _raw_read(self, frames):
        channels, _ = _split(self._channels)
        samplesize, _ = _split(self._samplesize)
        data = _ffi.new('signed char[]', channels * samplesize * frames)
        err = _lib.Pa_ReadStream(self._ptr, data, frames)
        if err == _lib.paInputOverflowed:
            overflowed = True
        else:
            _check(err)
            overflowed = False
        return _ffi.buffer(data), overflowed

class RawInputStream(_InputStreamBase):

    def __init__(self, samplerate=None, blocksize=None,
                 device=None, channels=None, dtype=None, latency=None,
                 extra_settings=None, callback=None, finished_callback=None,
                 clip_off=None, dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None):
        _StreamBase.__init__(self, kind='input', wrap_callback='buffer',
                             **_remove_self(locals()))

    read = _InputStreamBase._raw_read

class _OutputStreamBase(_StreamBase):

    @property
    def write_available(self):
        return _check(_lib.Pa_GetStreamWriteAvailable(self._ptr))

    def _raw_write(self, data):
        try:
            data = _ffi.from_buffer(data)
        except AttributeError:
            pass
        except TypeError:
            pass
        _, samplesize = _split(self._samplesize)
        _, channels = _split(self._channels)
        samples, remainder = divmod(len(data), samplesize)
        if remainder:
            raise ValueError('len(data) not divisible by samplesize')
        frames, remainder = divmod(samples, channels)
        if remainder:
            raise ValueError('Number of samples not divisible by channels')
        err = _lib.Pa_WriteStream(self._ptr, data, frames)
        if err == _lib.paOutputUnderflowed:
            underflowed = True
        else:
            _check(err)
            underflowed = False
        return underflowed

class RawOutputStream(_OutputStreamBase):

    def __init__(self, samplerate=None, blocksize=None,
                 device=None, channels=None, dtype=None, latency=None,
                 extra_settings=None, callback=None, finished_callback=None,
                 clip_off=None, dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None):
        _StreamBase.__init__(self, kind='output', wrap_callback='buffer',
                             **_remove_self(locals()))

    write = _OutputStreamBase._raw_write

class RawStream(RawInputStream, RawOutputStream):

    def __init__(self, samplerate=None, blocksize=None,
                 device=None, channels=None, dtype=None, latency=None,
                 extra_settings=None, callback=None, finished_callback=None,
                 clip_off=None, dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None):
        _StreamBase.__init__(self, kind='duplex', wrap_callback='buffer',
                             **_remove_self(locals()))

class InputStream(_InputStreamBase):

    def __init__(self, samplerate=None, blocksize=None,
                 device=None, channels=None, dtype=None, latency=None,
                 extra_settings=None, callback=None, finished_callback=None,
                 clip_off=None, dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None):
        _StreamBase.__init__(self, kind='input', wrap_callback='array',
                             **_remove_self(locals()))

    def read(self, frames):
        dtype, _ = _split(self._dtype)
        channels, _ = _split(self._channels)
        data, overflowed = _InputStreamBase._raw_read(self, frames)
        data = _array(data, channels, dtype)
        return data, overflowed

class OutputStream(_OutputStreamBase):

    def __init__(self, samplerate=None, blocksize=None,
                 device=None, channels=None, dtype=None, latency=None,
                 extra_settings=None, callback=None, finished_callback=None,
                 clip_off=None, dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None):
        _StreamBase.__init__(self, kind='output', wrap_callback='array',
                             **_remove_self(locals()))

    def write(self, data):
        import numpy as np
        data = np.asarray(data)
        _, dtype = _split(self._dtype)
        _, channels = _split(self._channels)
        if data.ndim < 2:
            data = data.reshape(-1, 1)
        elif data.ndim > 2:
            raise ValueError('data must be one- or two-dimensional')
        if data.shape[1] != channels:
            raise ValueError('number of channels must match')
        if data.dtype != dtype:
            raise TypeError('dtype mismatch: {!r} vs {!r}'.format(
                data.dtype.name, dtype))
        if not data.flags.c_contiguous:
            raise TypeError('data must be C-contiguous')
        return _OutputStreamBase._raw_write(self, data)

class Stream(InputStream, OutputStream):

    def __init__(self, samplerate=None, blocksize=None,
                 device=None, channels=None, dtype=None, latency=None,
                 extra_settings=None, callback=None, finished_callback=None,
                 clip_off=None, dither_off=None, never_drop_input=None,
                 prime_output_buffers_using_stream_callback=None):
        _StreamBase.__init__(self, kind='duplex', wrap_callback='array',
                             **_remove_self(locals()))

class DeviceList(tuple):

    __slots__ = ()

    def __repr__(self):
        idev = _get_device_id(default.device['input'], 'input')
        odev = _get_device_id(default.device['output'], 'output')
        digits = len(str(_lib.Pa_GetDeviceCount() - 1))
        hostapi_names = [hostapi['name'] for hostapi in query_hostapis()]

        def get_mark(idx):
            return (' ', '>', '<', '*')[(idx == idev) + 2 * (idx == odev)]

        text = '\n'.join(
            '{mark} {idx:{dig}} {name}, {ha} ({ins} in, {outs} out)'.format(
                mark=get_mark(info['index']),
                idx=info['index'],
                dig=digits,
                name=info['name'],
                ha=hostapi_names[info['hostapi']],
                ins=info['max_input_channels'],
                outs=info['max_output_channels'])
            for info in self)
        return text

class CallbackFlags:

    __slots__ = '_flags'

    def __init__(self, flags=0x0):
        self._flags = flags

    def __repr__(self):
        flags = str(self)
        if not flags:
            flags = 'no flags set'
        return f'<sounddevice.CallbackFlags: {flags}>'

    def __str__(self):
        return ', '.join(name.replace('_', ' ') for name in dir(self)
                         if not name.startswith('_') and getattr(self, name))

    def __bool__(self):
        return bool(self._flags)

    def __ior__(self, other):
        if not isinstance(other, CallbackFlags):
            return NotImplemented
        self._flags |= other._flags
        return self

    @property
    def input_underflow(self):
        return self._hasflag(_lib.paInputUnderflow)

    @input_underflow.setter
    def input_underflow(self, value):
        self._updateflag(_lib.paInputUnderflow, value)

    @property
    def input_overflow(self):
        return self._hasflag(_lib.paInputOverflow)

    @input_overflow.setter
    def input_overflow(self, value):
        self._updateflag(_lib.paInputOverflow, value)

    @property
    def output_underflow(self):
        return self._hasflag(_lib.paOutputUnderflow)

    @output_underflow.setter
    def output_underflow(self, value):
        self._updateflag(_lib.paOutputUnderflow, value)

    @property
    def output_overflow(self):
        return self._hasflag(_lib.paOutputOverflow)

    @output_overflow.setter
    def output_overflow(self, value):
        self._updateflag(_lib.paOutputOverflow, value)

    @property
    def priming_output(self):
        return self._hasflag(_lib.paPrimingOutput)

    def _hasflag(self, flag):
        return bool(self._flags & flag)

    def _updateflag(self, flag, value):
        if value:
            self._flags |= flag
        else:
            self._flags &= ~flag

class _InputOutputPair:

    _indexmapping = {'input': 0, 'output': 1}

    def __init__(self, parent, default_attr):
        self._pair = [None, None]
        self._parent = parent
        self._default_attr = default_attr

    def __getitem__(self, index):
        index = self._indexmapping.get(index, index)
        value = self._pair[index]
        if value is None:
            value = getattr(self._parent, self._default_attr)[index]
        return value

    def __setitem__(self, index, value):
        index = self._indexmapping.get(index, index)
        self._pair[index] = value

    def __repr__(self):
        return '[{0[0]!r}, {0[1]!r}]'.format(self)

class default:

    _pairs = 'device', 'channels', 'dtype', 'latency', 'extra_settings'

    device = None, None
    """Index or query string of default input/output device.

    If not overwritten, this is queried from PortAudio.

    See Also
    --------
    `default`, `query_devices()`, the *device* argument of `Stream`

    """
    channels = _default_channels = None, None
    """Default number of input/output channels.

    See Also
    --------
    `default`, `query_devices()`, the *channels* argument of `Stream`

    """
    dtype = _default_dtype = 'float32', 'float32'
    """Default data type used for input/output samples.

    The types ``'float32'``, ``'int32'``, ``'int16'``, ``'int8'`` and
    ``'uint8'`` can be used for all streams and functions.
    Additionally, `play()`, `rec()` and `playrec()` support
    ``'float64'`` (for convenience, data is merely converted from/to
    ``'float32'``) and `RawInputStream`, `RawOutputStream` and
    `RawStream` support ``'int24'`` (packed 24 bit format, which is
    *not* supported in NumPy!).

    See Also
    --------
    `default`, `numpy:numpy.dtype`, the *dtype* argument of `Stream`

    """
    latency = _default_latency = 'high', 'high'
    """See the *latency* argument of `Stream`."""
    extra_settings = _default_extra_settings = None, None
    """Host-API-specific input/output settings.

    See Also
    --------
    AsioSettings, CoreAudioSettings, WasapiSettings

    """
    samplerate = None
    """Sampling frequency in Hertz (= frames per second).

    See Also
    --------
    `default`, `query_devices()`

    """
    blocksize = _lib.paFramesPerBufferUnspecified
    """See the *blocksize* argument of `Stream`."""
    clip_off = False
    """Disable clipping.

    Set to ``True`` to disable default clipping of out of range samples.

    """
    dither_off = False
    """Disable dithering.

    Set to ``True`` to disable default dithering.

    """
    never_drop_input = False
    """Set behavior for input overflow of full-duplex streams.

    Set to ``True`` to request that where possible a full duplex stream
    will not discard overflowed input samples without calling the stream
    callback.  This flag is only valid for full-duplex callback streams
    (i.e. only `Stream` and `RawStream` and only if *callback* was
    specified; this includes `playrec()`) and only when used in
    combination with ``blocksize=0`` (the default).  Using this flag
    incorrectly results in an error being raised.  See also
    http://www.portaudio.com/docs/proposals/001-UnderflowOverflowHandling.html.

    """
    prime_output_buffers_using_stream_callback = False
    """How to fill initial output buffers.

    Set to ``True`` to call the stream callback to fill initial output
    buffers, rather than the default behavior of priming the buffers
    with zeros (silence).  This flag has no effect for input-only
    (`InputStream` and `RawInputStream`) and blocking read/write streams
    (i.e. if *callback* wasn't specified).  See also
    http://www.portaudio.com/docs/proposals/020-AllowCallbackToPrimeStream.html.

    """

    def __init__(self):
        for attr in self._pairs:

            vars(self)[attr] = _InputOutputPair(self, '_default_' + attr)

    def __setattr__(self, name, value):
        if name in self._pairs:
            getattr(self, name)._pair[:] = _split(value)
        elif name in dir(self) and name != 'reset':
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(
                "'default' object has no attribute " + repr(name))

    @property
    def _default_device(self):
        return (_lib.Pa_GetDefaultInputDevice(),
                _lib.Pa_GetDefaultOutputDevice())

    @property
    def hostapi(self):
        return _check(_lib.Pa_GetDefaultHostApi())

    def reset(self):
        vars(self).clear()
        self.__init__()

if not hasattr(_ffi, 'I_AM_FAKE'):

    default = default()

class PortAudioError(Exception):

    def __str__(self):
        errormsg = self.args[0] if self.args else ''
        if len(self.args) > 1:
            errormsg = f'{errormsg} [PaErrorCode {self.args[1]}]'
        if len(self.args) > 2:
            host_api, hosterror_code, hosterror_text = self.args[2]
            if host_api == _lib.paHostApiNotFound:
                hostname = '<host API not found>'
            elif host_api < 0:
                hostname = f'<error getting host API: {host_api}>'
            else:
                hostname = query_hostapis(host_api)['name']
            errormsg = "{}: '{}' [{} error {}]".format(
                errormsg, hosterror_text, hostname, hosterror_code)

        return errormsg

class CallbackStop(Exception):
    pass

class CallbackAbort(Exception):
    pass

class AsioSettings:

    def __init__(self, channel_selectors):
        if isinstance(channel_selectors, int):
            raise TypeError('channel_selectors must be a list or tuple')

        self._selectors = _ffi.new('int[]', channel_selectors)
        self._streaminfo = _ffi.new('PaAsioStreamInfo*', dict(
            size=_ffi.sizeof('PaAsioStreamInfo'),
            hostApiType=_lib.paASIO,
            version=1,
            flags=_lib.paAsioUseChannelSelectors,
            channelSelectors=self._selectors))

class CoreAudioSettings:

    def __init__(self, channel_map=None, change_device_parameters=False,
                 fail_if_conversion_required=False, conversion_quality='max'):
        conversion_dict = {
            'min':    _lib.paMacCoreConversionQualityMin,
            'low':    _lib.paMacCoreConversionQualityLow,
            'medium': _lib.paMacCoreConversionQualityMedium,
            'high':   _lib.paMacCoreConversionQualityHigh,
            'max':    _lib.paMacCoreConversionQualityMax,
        }

        if isinstance(channel_map, int):
            raise TypeError('channel_map must be a list or tuple')

        try:
            self._flags = conversion_dict[conversion_quality.lower()]
        except (KeyError, AttributeError) as e:
            raise ValueError('conversion_quality must be one of ' +
                             repr(list(conversion_dict))) from e
        if change_device_parameters:
            self._flags |= _lib.paMacCoreChangeDeviceParameters
        if fail_if_conversion_required:
            self._flags |= _lib.paMacCoreFailIfConversionRequired

        self._streaminfo = _ffi.new('PaMacCoreStreamInfo*')
        _lib.PaMacCore_SetupStreamInfo(self._streaminfo, self._flags)

        if channel_map is not None:

            self._channel_map = _ffi.new('SInt32[]', channel_map)
            if len(self._channel_map) == 0:
                raise TypeError('channel_map must not be empty')
            _lib.PaMacCore_SetupChannelMap(self._streaminfo,
                                           self._channel_map,
                                           len(self._channel_map))

class WasapiSettings:

    def __init__(self, exclusive=False, auto_convert=False, explicit_sample_format=False):
        flags = 0x0
        if exclusive:
            flags |= _lib.paWinWasapiExclusive
        if auto_convert:
            flags |= _lib.paWinWasapiAutoConvert
        if explicit_sample_format:
            flags |= _lib.paWinWasapiExplicitSampleFormat
        self._streaminfo = _ffi.new('PaWasapiStreamInfo*', dict(
            size=_ffi.sizeof('PaWasapiStreamInfo'),
            hostApiType=_lib.paWASAPI,
            version=1,
            flags=flags,
        ))

class _CallbackContext:

    blocksize = None
    data = None
    out = None
    frame = 0
    input_channels = output_channels = None
    input_dtype = output_dtype = None
    input_mapping = output_mapping = None
    silent_channels = None

    def __init__(self, loop=False):
        import threading
        try:
            import numpy
            assert numpy
        except ImportError as e:
            raise ImportError(
                'NumPy must be installed for play()/rec()/playrec()') from e
        self.loop = loop
        self.event = threading.Event()
        self.status = CallbackFlags()

    def check_data(self, data, mapping, device):
        import numpy as np
        data = np.asarray(data)
        if data.ndim < 2:
            data = data.reshape(-1, 1)
        elif data.ndim > 2:
            raise ValueError(
                'audio data to be played back must be one- or two-dimensional')
        frames, channels = data.shape
        dtype = _check_dtype(data.dtype)
        mapping_is_explicit = mapping is not None
        mapping, channels = _check_mapping(mapping, channels)
        if data.shape[1] == 1:
            pass
        elif data.shape[1] != len(mapping):
            raise ValueError(
                'number of output channels != size of output mapping')

        if (mapping_is_explicit and np.array_equal(mapping, [0]) and
                query_devices(device, 'output')['max_output_channels'] >= 2):
            channels = 2
        silent_channels = np.setdiff1d(np.arange(channels), mapping)
        if len(mapping) + len(silent_channels) != channels:
            raise ValueError('each channel may only appear once in mapping')

        self.data = data
        self.output_channels = channels
        self.output_dtype = dtype
        self.output_mapping = mapping
        self.silent_channels = silent_channels
        return frames

    def check_out(self, out, frames, channels, dtype, mapping):
        import numpy as np
        if out is None:
            if frames is None:
                raise TypeError('frames must be specified')
            if channels is None:
                channels = default.channels['input']
            if channels is None:
                if mapping is None:
                    raise TypeError(
                        'Unable to determine number of input channels')
                else:
                    channels = len(np.atleast_1d(mapping))
            if dtype is None:
                dtype = default.dtype['input']
            try:
                out = np.empty((frames, channels), dtype, order='C')
            except TypeError as e:
                from numbers import Integral
                if not isinstance(frames, Integral):
                    raise TypeError("'frames' must be an integer") from e
                if not isinstance(channels, Integral):
                    raise TypeError("'channels' must be an integer") from e
                raise e
        else:
            frames, channels = out.shape
            dtype = out.dtype
        dtype = _check_dtype(dtype)
        mapping, channels = _check_mapping(mapping, channels)
        if out.shape[1] != len(mapping):
            raise ValueError(
                'number of input channels != size of input mapping')

        self.out = out
        self.input_channels = channels
        self.input_dtype = dtype
        self.input_mapping = mapping
        return out, frames

    def callback_enter(self, status, data):
        self.status |= status
        self.blocksize = min(self.frames - self.frame, len(data))

    def read_indata(self, indata):

        for target, source in enumerate(self.input_mapping):

            self.out[self.frame:self.frame + self.blocksize, target] = \
                indata[:self.blocksize, source]

    def write_outdata(self, outdata):

        outdata[:self.blocksize, self.output_mapping] = \
            self.data[self.frame:self.frame + self.blocksize]
        outdata[:self.blocksize, self.silent_channels] = 0
        if self.loop and self.blocksize < len(outdata):
            self.frame = 0
            outdata = outdata[self.blocksize:]
            self.blocksize = min(self.frames, len(outdata))
            self.write_outdata(outdata)
        else:
            outdata[self.blocksize:] = 0

    def callback_exit(self):
        if not self.blocksize:
            raise CallbackAbort
        self.frame += self.blocksize

    def finished_callback(self):
        self.event.set()

        self.data = None
        self.out = None

        self.stream._callback = None
        self.stream._finished_callback = None

    def start_stream(self, StreamClass, samplerate, channels, dtype, callback,
                     blocking, **kwargs):
        stop()
        self.stream = StreamClass(samplerate=samplerate,
                                  channels=channels,
                                  dtype=dtype,
                                  callback=callback,
                                  finished_callback=self.finished_callback,
                                  **kwargs)
        self.stream.start()
        global _last_callback
        _last_callback = self
        if blocking:
            self.wait()

    def wait(self, ignore_errors=True):
        try:
            self.event.wait()
        finally:
            self.stream.close(ignore_errors)
        return self.status if self.status else None

def _remove_self(d):
    d = d.copy()
    del d['self']
    return d

def _check_mapping(mapping, channels):
    import numpy as np
    if mapping is None:
        mapping = np.arange(channels)
    else:
        mapping = np.array(mapping, copy=True)
        mapping = np.atleast_1d(mapping)
        if mapping.min() < 1:
            raise ValueError('channel numbers must not be < 1')
        channels = mapping.max()
        mapping -= 1
    return mapping, channels

def _check_dtype(dtype):
    import numpy as np
    dtype = np.dtype(dtype).name
    if dtype in _sampleformats:
        pass
    elif dtype == 'float64':
        dtype = 'float32'
    else:
        raise TypeError('Unsupported data type: ' + repr(dtype))
    return dtype

def _get_stream_parameters(kind, device, channels, dtype, latency,
                           extra_settings, samplerate):
    assert kind in ('input', 'output')
    if device is None:
        device = default.device
    device = _get_device_id(device, kind, raise_on_error=True)
    if channels is None:
        channels = default.channels
    channels = _select_input_or_output(channels, kind)
    if dtype is None:
        dtype = default.dtype
    dtype = _select_input_or_output(dtype, kind)
    if latency is None:
        latency = default.latency
    latency = _select_input_or_output(latency, kind)
    if extra_settings is None:
        extra_settings = default.extra_settings
    extra_settings = _select_input_or_output(extra_settings, kind)
    if samplerate is None:
        samplerate = default.samplerate

    info = query_devices(device)
    if channels is None:
        channels = info['max_' + kind + '_channels']
    try:

        dtype = _sys.modules['numpy'].dtype(dtype).name
    except Exception:
        pass
    try:
        sampleformat = _sampleformats[dtype]
    except KeyError as e:
        raise ValueError('Invalid ' + kind + ' sample format') from e
    samplesize = _check(_lib.Pa_GetSampleSize(sampleformat))
    if latency in ('low', 'high'):
        latency = info['default_' + latency + '_' + kind + '_latency']
    if samplerate is None:
        samplerate = info['default_samplerate']
    parameters = _ffi.new('PaStreamParameters*', (
        device, channels, sampleformat, latency,
        extra_settings._streaminfo if extra_settings else _ffi.NULL))
    return parameters, dtype, samplesize, samplerate

def _wrap_callback(callback, *args):
    args = args[:-1] + (CallbackFlags(args[-1]),)
    try:
        callback(*args)
    except CallbackStop:
        return _lib.paComplete
    except CallbackAbort:
        return _lib.paAbort
    return _lib.paContinue

def _buffer(ptr, frames, channels, samplesize):
    return _ffi.buffer(ptr, frames * channels * samplesize)

def _array(buffer, channels, dtype):
    import numpy as np
    data = np.frombuffer(buffer, dtype=dtype)
    data.shape = -1, channels
    return data

def _split(value):
    if isinstance(value, (str, bytes)):

        return value, value
    try:
        invalue, outvalue = value
    except TypeError:
        invalue = outvalue = value
    except ValueError as e:
        raise ValueError(
            f'Only single values and pairs are allowed, not {value!r}') from e
    return invalue, outvalue

def _check(err, msg=''):
    if err >= 0:
        return err

    errormsg = _ffi.string(_lib.Pa_GetErrorText(err)).decode()
    if msg:
        errormsg = f'{msg}: {errormsg}'

    if err == _lib.paUnanticipatedHostError:

        info = _lib.Pa_GetLastHostErrorInfo()
        host_api = _lib.Pa_HostApiTypeIdToHostApiIndex(info.hostApiType)
        hosterror_text = _ffi.string(info.errorText).decode()
        hosterror_info = host_api, info.errorCode, hosterror_text
        raise PortAudioError(errormsg, err, hosterror_info)

    raise PortAudioError(errormsg, err)

def _select_input_or_output(value_or_pair, kind):
    ivalue, ovalue = _split(value_or_pair)
    if kind == 'input':
        return ivalue
    elif kind == 'output':
        return ovalue
    assert False

def _get_device_id(id_or_query_string, kind, raise_on_error=False):
    assert kind in ('input', 'output', None)

    if id_or_query_string is None:
        id_or_query_string = default.device

    idev, odev = _split(id_or_query_string)
    if kind == 'input':
        id_or_query_string = idev
    elif kind == 'output':
        id_or_query_string = odev
    else:
        if idev == odev:
            id_or_query_string = idev
        else:
            raise ValueError('Input and output device are different: {!r}'
                             .format(id_or_query_string))

    if isinstance(id_or_query_string, int):
        return id_or_query_string
    device_list = []
    for id, info in enumerate(query_devices()):
        if not kind or info['max_' + kind + '_channels'] > 0:
            hostapi_info = query_hostapis(info['hostapi'])
            device_list.append((id, info['name'], hostapi_info['name']))

    query_string = id_or_query_string.lower()
    substrings = query_string.split()
    matches = []
    exact_device_matches = []
    for id, device_string, hostapi_string in device_list:
        full_string = device_string + ', ' + hostapi_string
        pos = 0
        for substring in substrings:
            pos = full_string.lower().find(substring, pos)
            if pos < 0:
                break
            pos += len(substring)
        else:
            matches.append((id, full_string))
            if query_string in [device_string.lower(), full_string.lower()]:
                exact_device_matches.append(id)

    if kind is None:
        kind = 'input/output'

    if not matches:
        if raise_on_error:
            raise ValueError(
                'No ' + kind + ' device matching ' + repr(id_or_query_string))
        else:
            return -1
    if len(matches) > 1:
        if len(exact_device_matches) == 1:
            return exact_device_matches[0]
        if raise_on_error:
            raise ValueError('Multiple ' + kind + ' devices found for ' +
                             repr(id_or_query_string) + ':\n' +
                             '\n'.join(f'[{id}] {name}'
                                       for id, name in matches))
        else:
            return -1
    return matches[0][0]

def _initialize():
    old_stderr = None
    try:
        old_stderr = _os.dup(2)
        devnull = _os.open(_os.devnull, _os.O_WRONLY)
        _os.dup2(devnull, 2)
        _os.close(devnull)
    except OSError:
        pass
    try:
        _check(_lib.Pa_Initialize(), 'Error initializing PortAudio')
        global _initialized
        _initialized += 1
    finally:
        if old_stderr is not None:
            _os.dup2(old_stderr, 2)
            _os.close(old_stderr)

def _terminate():
    global _initialized
    _check(_lib.Pa_Terminate(), 'Error terminating PortAudio')
    _initialized -= 1

def _exit_handler():
    assert _initialized >= 0

    if _last_callback:

        _last_callback.stream.stop()
        _last_callback.stream.close()

    while _initialized:
        _terminate()

_atexit.register(_exit_handler)
_initialize()

if __name__ == '__main__':
    print(query_devices())
