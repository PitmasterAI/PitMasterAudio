"""Cómputo en GPU por Vulkan, sin CUDA ni drivers propietarios.

Habla libvulkan.so.1 directamente (ctypes) y lanza shaders SPIR-V compilados con
glslc. Vale igual para AMD (RADV), Intel, NVIDIA y llvmpipe: lo único que hace
falta es que el aparato tenga un driver Vulkan, que es lo normal en Linux,
Windows y Android.

Operaciones que expone (todas sobre float32 entrelazado):

    escalar(x, g)                  x * g
    mul_por_vector(x, gan, canales) x * gan[trama]
    estereo_ms(x, gm, gl)          matriz medio/lado
    saturar(x, k)                  tanh(x * k)
    pico_real(x, taps, desfases, ktaps)  envolvente de pico real por fases
"""
import ctypes
import os
import struct
import threading

# Vulkan comparte pool de descriptores y command buffer: un hilo a la vez
_CERROJO = threading.RLock()

import numpy as np

# ------------------------------------------------------------------ constantes
VK_SUCCESS = 0
VK_STRUCTURE_TYPE_APPLICATION_INFO = 0
VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO = 1
VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO = 2
VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO = 3
VK_STRUCTURE_TYPE_SUBMIT_INFO = 4
VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO = 5
VK_STRUCTURE_TYPE_FENCE_CREATE_INFO = 8
VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO = 12
VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO = 15
VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO = 18
VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO = 19
VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO = 22
VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO = 24
VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET = 23
VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO = 29
VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO = 30
VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO = 39
VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO = 40
VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO = 42
VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER = 44

VK_QUEUE_COMPUTE_BIT = 0x00000002
VK_BUFFER_USAGE_TRANSFER_SRC_BIT = 0x00000001
VK_BUFFER_USAGE_TRANSFER_DST_BIT = 0x00000002
VK_BUFFER_USAGE_STORAGE_BUFFER_BIT = 0x00000020
VK_SHARING_MODE_EXCLUSIVE = 0
VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT = 0x00000002
VK_MEMORY_PROPERTY_HOST_COHERENT_BIT = 0x00000004
VK_DESCRIPTOR_TYPE_STORAGE_BUFFER = 7
VK_SHADER_STAGE_COMPUTE_BIT = 0x00000020
VK_PIPELINE_BIND_POINT_COMPUTE = 1
VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT = 0x00000002
VK_COMMAND_BUFFER_LEVEL_PRIMARY = 0
VK_PIPELINE_STAGE_ALL_COMMANDS_BIT = 0x00010000
VK_ACCESS_MEMORY_READ_BIT = 0x00008000


# -------------------------------------------------------------------- structs
class VkApplicationInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("pApplicationName", ctypes.c_char_p), ("applicationVersion", ctypes.c_uint32),
                ("pEngineName", ctypes.c_char_p), ("engineVersion", ctypes.c_uint32),
                ("apiVersion", ctypes.c_uint32)]


class VkInstanceCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("pApplicationInfo", ctypes.c_void_p),
                ("enabledLayerCount", ctypes.c_uint32), ("ppEnabledLayerNames", ctypes.c_void_p),
                ("enabledExtensionCount", ctypes.c_uint32),
                ("ppEnabledExtensionNames", ctypes.c_void_p)]


class VkExtent3D(ctypes.Structure):
    _fields_ = [("width", ctypes.c_uint32), ("height", ctypes.c_uint32),
                ("depth", ctypes.c_uint32)]


class VkQueueFamilyProperties(ctypes.Structure):
    _fields_ = [("queueFlags", ctypes.c_uint32), ("queueCount", ctypes.c_uint32),
                ("timestampValidBits", ctypes.c_uint32),
                ("minImageTransferGranularity", VkExtent3D)]


class VkDeviceQueueCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("queueFamilyIndex", ctypes.c_uint32),
                ("queueCount", ctypes.c_uint32), ("pQueuePriorities", ctypes.c_void_p)]


class VkDeviceCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("queueCreateInfoCount", ctypes.c_uint32),
                ("pQueueCreateInfos", ctypes.c_void_p),
                ("enabledLayerCount", ctypes.c_uint32), ("ppEnabledLayerNames", ctypes.c_void_p),
                ("enabledExtensionCount", ctypes.c_uint32),
                ("ppEnabledExtensionNames", ctypes.c_void_p),
                ("pEnabledFeatures", ctypes.c_void_p)]


class VkBufferCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("size", ctypes.c_uint64),
                ("usage", ctypes.c_uint32), ("sharingMode", ctypes.c_uint32),
                ("queueFamilyIndexCount", ctypes.c_uint32),
                ("pQueueFamilyIndices", ctypes.c_void_p)]


class VkMemoryRequirements(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint64), ("alignment", ctypes.c_uint64),
                ("memoryTypeBits", ctypes.c_uint32)]


class VkMemoryType(ctypes.Structure):
    _fields_ = [("propertyFlags", ctypes.c_uint32), ("heapIndex", ctypes.c_uint32)]


class VkMemoryHeap(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint64), ("flags", ctypes.c_uint32)]


class VkPhysicalDeviceMemoryProperties(ctypes.Structure):
    _fields_ = [("memoryTypeCount", ctypes.c_uint32),
                ("memoryTypes", VkMemoryType * 32),
                ("memoryHeapCount", ctypes.c_uint32),
                ("memoryHeaps", VkMemoryHeap * 16)]


class VkMemoryAllocateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("allocationSize", ctypes.c_uint64), ("memoryTypeIndex", ctypes.c_uint32)]


class VkShaderModuleCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("codeSize", ctypes.c_size_t),
                ("pCode", ctypes.c_void_p)]


class VkDescriptorSetLayoutBinding(ctypes.Structure):
    _fields_ = [("binding", ctypes.c_uint32), ("descriptorType", ctypes.c_uint32),
                ("descriptorCount", ctypes.c_uint32), ("stageFlags", ctypes.c_uint32),
                ("pImmutableSamplers", ctypes.c_void_p)]


class VkDescriptorSetLayoutCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("bindingCount", ctypes.c_uint32),
                ("pBindings", ctypes.c_void_p)]


class VkPushConstantRange(ctypes.Structure):
    _fields_ = [("stageFlags", ctypes.c_uint32), ("offset", ctypes.c_uint32),
                ("size", ctypes.c_uint32)]


class VkPipelineLayoutCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("setLayoutCount", ctypes.c_uint32),
                ("pSetLayouts", ctypes.c_void_p), ("pushConstantRangeCount", ctypes.c_uint32),
                ("pPushConstantRanges", ctypes.c_void_p)]


class VkPipelineShaderStageCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("stage", ctypes.c_uint32),
                ("module", ctypes.c_void_p), ("pName", ctypes.c_char_p),
                ("pSpecializationInfo", ctypes.c_void_p)]


class VkComputePipelineCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("stage", VkPipelineShaderStageCreateInfo),
                ("layout", ctypes.c_void_p), ("basePipelineHandle", ctypes.c_void_p),
                ("basePipelineIndex", ctypes.c_int32)]


class VkDescriptorPoolSize(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("descriptorCount", ctypes.c_uint32)]


class VkDescriptorPoolCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("maxSets", ctypes.c_uint32),
                ("poolSizeCount", ctypes.c_uint32), ("pPoolSizes", ctypes.c_void_p)]


class VkDescriptorSetAllocateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("descriptorPool", ctypes.c_void_p), ("descriptorSetCount", ctypes.c_uint32),
                ("pSetLayouts", ctypes.c_void_p)]


class VkDescriptorBufferInfo(ctypes.Structure):
    _fields_ = [("buffer", ctypes.c_void_p), ("offset", ctypes.c_uint64),
                ("range", ctypes.c_uint64)]


class VkWriteDescriptorSet(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("dstSet", ctypes.c_void_p), ("dstBinding", ctypes.c_uint32),
                ("dstArrayElement", ctypes.c_uint32), ("descriptorCount", ctypes.c_uint32),
                ("descriptorType", ctypes.c_uint32), ("pImageInfo", ctypes.c_void_p),
                ("pBufferInfo", ctypes.c_void_p), ("pTexelBufferView", ctypes.c_void_p)]


class VkCommandPoolCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("queueFamilyIndex", ctypes.c_uint32)]


class VkCommandBufferAllocateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("commandPool", ctypes.c_void_p), ("level", ctypes.c_uint32),
                ("commandBufferCount", ctypes.c_uint32)]


class VkCommandBufferBeginInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32), ("pInheritanceInfo", ctypes.c_void_p)]


class VkBufferMemoryBarrier(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("srcAccessMask", ctypes.c_uint32), ("dstAccessMask", ctypes.c_uint32),
                ("srcQueueFamilyIndex", ctypes.c_uint32),
                ("dstQueueFamilyIndex", ctypes.c_uint32), ("buffer", ctypes.c_void_p),
                ("offset", ctypes.c_uint64), ("size", ctypes.c_uint64)]


class VkSubmitInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("waitSemaphoreCount", ctypes.c_uint32), ("pWaitSemaphores", ctypes.c_void_p),
                ("pWaitDstStageMask", ctypes.c_void_p), ("commandBufferCount", ctypes.c_uint32),
                ("pCommandBuffers", ctypes.c_void_p), ("signalSemaphoreCount", ctypes.c_uint32),
                ("pSignalSemaphores", ctypes.c_void_p)]


class VkFenceCreateInfo(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_uint32), ("pNext", ctypes.c_void_p),
                ("flags", ctypes.c_uint32)]


# ------------------------------------------------------------------- el motor
class Vulkan:
    """Contexto Vulkan mínimo para lanzar shaders de cómputo."""

    def __init__(self, carpeta_shaders=None):
        self.listo = False
        self.nombre = ''
        self.error = ''
        self._shaders = {}
        self._pozo = {}        # buffers ya creados por tamaño (se reutilizan)
        self._pozo_i = {}      # siguiente hueco libre dentro de la llamada en curso
        carpeta = carpeta_shaders or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vk')
        self.carpeta = carpeta
        try:
            self._abrir()
            self.listo = True
        except Exception as e:                       # sin driver Vulkan se sigue en CPU
            self.error = '%s: %s' % (type(e).__name__, e)
            self.listo = False

    def _prototipos(self):
        """Firma de cada función: sin esto ctypes recorta los punteros y revienta."""
        vk = self.vk
        V = ctypes.c_void_p
        U = ctypes.c_uint32
        U64 = ctypes.c_uint64
        firmas = {
            'vkCreateInstance': [V, V, V],
            'vkEnumeratePhysicalDevices': [V, V, V],
            'vkGetPhysicalDeviceProperties': [V, V],
            'vkGetPhysicalDeviceQueueFamilyProperties': [V, V, V],
            'vkCreateDevice': [V, V, V, V],
            'vkGetDeviceQueue': [V, U, U, V],
            'vkGetPhysicalDeviceMemoryProperties': [V, V],
            'vkCreateCommandPool': [V, V, V, V],
            'vkAllocateCommandBuffers': [V, V, V],
            'vkCreateDescriptorPool': [V, V, V, V],
            'vkCreateFence': [V, V, V, V],
            'vkCreateShaderModule': [V, V, V, V],
            'vkCreateDescriptorSetLayout': [V, V, V, V],
            'vkCreatePipelineLayout': [V, V, V, V],
            'vkCreateComputePipelines': [V, V, U, V, V, V],
            'vkGetBufferMemoryRequirements': [V, V, V],
            'vkCreateBuffer': [V, V, V, V],
            'vkAllocateMemory': [V, V, V, V],
            'vkBindBufferMemory': [V, V, V, U64],
            'vkMapMemory': [V, V, U64, U64, U, V],
            'vkUnmapMemory': [V, V],
            'vkDestroyBuffer': [V, V, V],
            'vkFreeMemory': [V, V, V],
            'vkResetDescriptorPool': [V, V, U],
            'vkAllocateDescriptorSets': [V, V, V],
            'vkUpdateDescriptorSets': [V, U, V, U, V],
            'vkBeginCommandBuffer': [V, V],
            'vkCmdBindPipeline': [V, U, V],
            'vkCmdBindDescriptorSets': [V, U, V, U, U, V, U, V],
            'vkCmdPushConstants': [V, V, U, U, U, V],
            'vkCmdDispatch': [V, U, U, U],
            'vkCmdPipelineBarrier': [V, U, U, U, U, V, U, V, U, V],
            'vkEndCommandBuffer': [V],
            'vkResetFences': [V, U, V],
            'vkQueueSubmit': [V, U, V, V],
            'vkWaitForFences': [V, U, V, U, U64],
        }
        for nombre, args in firmas.items():
            f = getattr(vk, nombre)
            f.restype = ctypes.c_int
            f.argtypes = args

    # ------------------------------------------------------------- arranque
    def _abrir(self):
        # El cargador de Vulkan se llama distinto en cada sistema. Con el nombre de
        # Linux fijo, en Windows no se cargaba nunca y la tarjeta se quedaba sin usar
        # (un RTX 3090 parado mientras el panel iba por CPU, el doble de lento).
        self.vk = None
        errores = []
        for nombre in ('vulkan-1.dll', 'vulkan-1', 'libvulkan.so.1',
                       'libvulkan.so', 'libvulkan.1.dylib', 'libvulkan.dylib'):
            try:
                self.vk = ctypes.CDLL(nombre)
                break
            except OSError as e:
                errores.append('%s: %s' % (nombre, e))
        if self.vk is None:
            raise RuntimeError('sin cargador de Vulkan (%s)' % '; '.join(errores))
        vk = self.vk
        self._prototipos()
        vk.vkCreateInstance.restype = ctypes.c_int
        app = VkApplicationInfo(sType=VK_STRUCTURE_TYPE_APPLICATION_INFO, pNext=None,
                                pApplicationName=b'PitMasterAudio', applicationVersion=1,
                                pEngineName=b'vk_compute', engineVersion=1, apiVersion=4194304)
        info = VkInstanceCreateInfo(sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, pNext=None,
                                    flags=0, pApplicationInfo=ctypes.cast(ctypes.byref(app),
                                                                          ctypes.c_void_p),
                                    enabledLayerCount=0, ppEnabledLayerNames=None,
                                    enabledExtensionCount=0, ppEnabledExtensionNames=None)
        inst = ctypes.c_void_p()
        if vk.vkCreateInstance(ctypes.byref(info), None, ctypes.byref(inst)) != VK_SUCCESS:
            raise RuntimeError('vkCreateInstance')
        self.instancia = inst

        cuenta = ctypes.c_uint32(0)
        vk.vkEnumeratePhysicalDevices(inst, ctypes.byref(cuenta), None)
        if cuenta.value == 0:
            raise RuntimeError('sin dispositivos Vulkan')
        dispositivos = (ctypes.c_void_p * cuenta.value)()
        vk.vkEnumeratePhysicalDevices(inst, ctypes.byref(cuenta), dispositivos)
        self.fisico = dispositivos[0]

        # nombre del aparato (VkPhysicalDeviceProperties: deviceName va tras 5 uint32)
        crudo = ctypes.create_string_buffer(4096)
        vk.vkGetPhysicalDeviceProperties(self.fisico, crudo)
        self.nombre = crudo.raw[20:276].split(b'\x00')[0].decode('utf-8', 'replace')
        # VkPhysicalDeviceProperties: apiVersion, driverVersion, vendorID, deviceID, deviceType
        self.tipo = int.from_bytes(crudo.raw[16:20], 'little')

        # cola de cómputo
        nfam = ctypes.c_uint32(0)
        vk.vkGetPhysicalDeviceQueueFamilyProperties(self.fisico, ctypes.byref(nfam), None)
        familias = (VkQueueFamilyProperties * nfam.value)()
        vk.vkGetPhysicalDeviceQueueFamilyProperties(self.fisico, ctypes.byref(nfam), familias)
        self.familia = None
        for i in range(nfam.value):
            if familias[i].queueFlags & VK_QUEUE_COMPUTE_BIT:
                self.familia = i
                break
        if self.familia is None:
            raise RuntimeError('sin cola de cómputo')

        prioridad = ctypes.c_float(1.0)
        cola = VkDeviceQueueCreateInfo(sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                       pNext=None, flags=0, queueFamilyIndex=self.familia,
                                       queueCount=1,
                                       pQueuePriorities=ctypes.cast(ctypes.byref(prioridad),
                                                                    ctypes.c_void_p))
        crear = VkDeviceCreateInfo(sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, pNext=None,
                                   flags=0, queueCreateInfoCount=1,
                                   pQueueCreateInfos=ctypes.cast(ctypes.byref(cola),
                                                                 ctypes.c_void_p),
                                   enabledLayerCount=0, ppEnabledLayerNames=None,
                                   enabledExtensionCount=0, ppEnabledExtensionNames=None,
                                   pEnabledFeatures=None)
        self.dispositivo = ctypes.c_void_p()
        if vk.vkCreateDevice(self.fisico, ctypes.byref(crear), None,
                             ctypes.byref(self.dispositivo)) != VK_SUCCESS:
            raise RuntimeError('vkCreateDevice')
        self.cola = ctypes.c_void_p()
        vk.vkGetDeviceQueue(self.dispositivo, self.familia, 0, ctypes.byref(self.cola))

        self.memorias = VkPhysicalDeviceMemoryProperties()
        vk.vkGetPhysicalDeviceMemoryProperties(self.fisico, ctypes.byref(self.memorias))

        self.pool = ctypes.c_void_p()
        crear_pool = VkCommandPoolCreateInfo(sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                             pNext=None,
                                             flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
                                             queueFamilyIndex=self.familia)
        if vk.vkCreateCommandPool(self.dispositivo, ctypes.byref(crear_pool), None,
                                  ctypes.byref(self.pool)) != VK_SUCCESS:
            raise RuntimeError('vkCreateCommandPool')
        asignar = VkCommandBufferAllocateInfo(sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                                             pNext=None, commandPool=self.pool,
                                             level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                             commandBufferCount=1)
        self.cmd = ctypes.c_void_p()
        vk.vkAllocateCommandBuffers(self.dispositivo, ctypes.byref(asignar),
                                    ctypes.byref(self.cmd))

        tam = VkDescriptorPoolSize(type=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, descriptorCount=32)
        crear_dp = VkDescriptorPoolCreateInfo(sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
                                              pNext=None, flags=0, maxSets=8, poolSizeCount=1,
                                              pPoolSizes=ctypes.cast(ctypes.byref(tam),
                                                                     ctypes.c_void_p))
        self.pool_desc = ctypes.c_void_p()
        if vk.vkCreateDescriptorPool(self.dispositivo, ctypes.byref(crear_dp), None,
                                     ctypes.byref(self.pool_desc)) != VK_SUCCESS:
            raise RuntimeError('vkCreateDescriptorPool')

        crear_fence = VkFenceCreateInfo(sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO, pNext=None,
                                        flags=0)
        self.fence = ctypes.c_void_p()
        vk.vkCreateFence(self.dispositivo, ctypes.byref(crear_fence), None,
                         ctypes.byref(self.fence))

    # ----------------------------------------------------------- tuberías
    def _tuberia(self, shader, n_buffers, push_tam):
        clave = (shader, n_buffers, push_tam)
        if clave in self._shaders:
            return self._shaders[clave]
        vk = self.vk
        ruta = os.path.join(self.carpeta, shader + '.spv')
        with open(ruta, 'rb') as f:
            codigo = f.read()
        buf = ctypes.create_string_buffer(codigo, len(codigo))
        info_mod = VkShaderModuleCreateInfo(sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
                                            pNext=None, flags=0, codeSize=len(codigo),
                                            pCode=ctypes.cast(buf, ctypes.c_void_p))
        modulo = ctypes.c_void_p()
        if vk.vkCreateShaderModule(self.dispositivo, ctypes.byref(info_mod), None,
                                   ctypes.byref(modulo)) != VK_SUCCESS:
            raise RuntimeError('vkCreateShaderModule ' + shader)

        enlaces = (VkDescriptorSetLayoutBinding * n_buffers)()
        for i in range(n_buffers):
            enlaces[i] = VkDescriptorSetLayoutBinding(binding=i,
                                                      descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                                                      descriptorCount=1,
                                                      stageFlags=VK_SHADER_STAGE_COMPUTE_BIT,
                                                      pImmutableSamplers=None)
        info_dsl = VkDescriptorSetLayoutCreateInfo(
            sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO, pNext=None, flags=0,
            bindingCount=n_buffers,
            pBindings=ctypes.cast(enlaces, ctypes.c_void_p))
        layout_desc = ctypes.c_void_p()
        vk.vkCreateDescriptorSetLayout(self.dispositivo, ctypes.byref(info_dsl), None,
                                      ctypes.byref(layout_desc))

        rango = VkPushConstantRange(stageFlags=VK_SHADER_STAGE_COMPUTE_BIT, offset=0,
                                    size=push_tam)
        info_layout = VkPipelineLayoutCreateInfo(
            sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO, pNext=None, flags=0,
            setLayoutCount=1, pSetLayouts=ctypes.cast(ctypes.byref(layout_desc),
                                                      ctypes.c_void_p),
            pushConstantRangeCount=1 if push_tam else 0,
            pPushConstantRanges=ctypes.cast(ctypes.byref(rango), ctypes.c_void_p) if push_tam
            else None)
        layout = ctypes.c_void_p()
        if vk.vkCreatePipelineLayout(self.dispositivo, ctypes.byref(info_layout), None,
                                     ctypes.byref(layout)) != VK_SUCCESS:
            raise RuntimeError('vkCreatePipelineLayout ' + shader)

        etapa = VkPipelineShaderStageCreateInfo(
            sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, pNext=None, flags=0,
            stage=VK_SHADER_STAGE_COMPUTE_BIT, module=modulo, pName=b'main',
            pSpecializationInfo=None)
        info_pipe = VkComputePipelineCreateInfo(
            sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO, pNext=None, flags=0,
            stage=etapa, layout=layout, basePipelineHandle=None, basePipelineIndex=-1)
        tuberia = ctypes.c_void_p()
        if vk.vkCreateComputePipelines(self.dispositivo, None, 1, ctypes.byref(info_pipe),
                                       None, ctypes.byref(tuberia)) != VK_SUCCESS:
            raise RuntimeError('vkCreateComputePipelines ' + shader)
        self._shaders[clave] = (tuberia, layout, layout_desc, buf, modulo)
        return self._shaders[clave]

    # ------------------------------------------------------------ memoria
    def _tipo_memoria(self, requisitos):
        for i in range(self.memorias.memoryTypeCount):
            if not (requisitos.memoryTypeBits & (1 << i)):
                continue
            flags = self.memorias.memoryTypes[i].propertyFlags
            if (flags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT
                    and flags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT):
                return i
        raise RuntimeError('sin memoria visible por el anfitrión')

    def _buffer(self, datos, tam=None):
        vk = self.vk
        if tam is None:
            tam = len(datos)
        tam = max(tam, 16)
        info = VkBufferCreateInfo(sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, pNext=None,
                                  flags=0, size=tam,
                                  usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT
                                        | VK_BUFFER_USAGE_TRANSFER_SRC_BIT
                                        | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
                                  sharingMode=VK_SHARING_MODE_EXCLUSIVE,
                                  queueFamilyIndexCount=0, pQueueFamilyIndices=None)
        buf = ctypes.c_void_p()
        if vk.vkCreateBuffer(self.dispositivo, ctypes.byref(info), None,
                             ctypes.byref(buf)) != VK_SUCCESS:
            raise RuntimeError('vkCreateBuffer')
        req = VkMemoryRequirements()
        vk.vkGetBufferMemoryRequirements(self.dispositivo, buf, ctypes.byref(req))
        asignar = VkMemoryAllocateInfo(sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, pNext=None,
                                       allocationSize=req.size,
                                       memoryTypeIndex=self._tipo_memoria(req))
        memoria = ctypes.c_void_p()
        if vk.vkAllocateMemory(self.dispositivo, ctypes.byref(asignar), None,
                               ctypes.byref(memoria)) != VK_SUCCESS:
            raise RuntimeError('vkAllocateMemory')
        vk.vkBindBufferMemory(self.dispositivo, buf, memoria, 0)
        datos_ptr = ctypes.c_void_p()
        vk.vkMapMemory(self.dispositivo, memoria, 0, tam, 0, ctypes.byref(datos_ptr))
        if datos:
            ctypes.memmove(datos_ptr, datos, len(datos))
        return buf, memoria, datos_ptr, tam

    def _liberar(self, buf, memoria):
        self.vk.vkUnmapMemory(self.dispositivo, memoria)
        self.vk.vkDestroyBuffer(self.dispositivo, buf, None)
        self.vk.vkFreeMemory(self.dispositivo, memoria, None)

    def _del_pozo(self, tam_bytes):
        """Buffer creado y mapeado del tamaño pedido, reutilizado entre llamadas.

        Crear y mapear memoria en cada lanzamiento cuesta más que el propio cálculo;
        en las tarjetas NVIDIA era la diferencia entre 40 y 95 ms por llamada.
        """
        tam = max(tam_bytes, 16)
        pila = self._pozo.get(tam)
        if pila is None:
            pila = self._pozo[tam] = []
        i = self._pozo_i.get(tam, 0)
        if i >= len(pila):
            pila.append(self._buffer(b'', tam))
        self._pozo_i[tam] = i + 1
        return pila[i]

    def _subir(self, datos):
        """Copia `datos` a un buffer del pozo y lo devuelve."""
        b = self._del_pozo(len(datos) if datos else 16)
        if datos:
            ctypes.memmove(b[2], datos, len(datos))
        return b

    def poda(self, maximo=24):
        """Suelta los buffers de los tamaños que ya no se usan (deja los más repetidos)."""
        if len(self._pozo) <= maximo:
            return
        for tam in list(self._pozo.keys())[:-maximo]:
            for buf, memoria, _ptr, _t in self._pozo.pop(tam, []):
                try:
                    self._liberar(buf, memoria)
                except Exception:
                    pass

    # ------------------------------------------------------------- lanzar
    def ejecutar(self, shader, entradas, salida_bytes, push, grupos):
        """Un solo hilo a la vez: el pool de descriptores y el command buffer son compartidos."""
        with _CERROJO:
            self.poda()
            return self._ejecutar_bloque(shader, entradas, salida_bytes, push, grupos)

    def _ejecutar_bloque(self, shader, entradas, salida_bytes, push, grupos):
        """entradas: lista de bytes (float32); salida_bytes: tamaño de la salida."""
        tuberia, layout, layout_desc, _buf, _mod = self._tuberia(shader, len(entradas) + 1,
                                                                 len(push))
        vk = self.vk
        creados = []
        try:
            vk.vkResetDescriptorPool(self.dispositivo, self.pool_desc, 0)
            self._pozo_i.clear()            # dentro de una llamada, cada buffer es distinto
            for datos in entradas:
                creados.append(self._subir(datos))
            salida = self._del_pozo(salida_bytes)
            creados.append(salida)

            sets = ctypes.c_void_p()
            asignar = VkDescriptorSetAllocateInfo(
                sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO, pNext=None,
                descriptorPool=self.pool_desc, descriptorSetCount=1,
                pSetLayouts=ctypes.cast(ctypes.byref(layout_desc), ctypes.c_void_p))
            vk.vkAllocateDescriptorSets(self.dispositivo, ctypes.byref(asignar),
                                        ctypes.byref(sets))

            escrituras = (VkWriteDescriptorSet * len(creados))()
            infos = (VkDescriptorBufferInfo * len(creados))()
            for i, (buf, _mem, _ptr, tam) in enumerate(creados):
                infos[i] = VkDescriptorBufferInfo(buffer=buf, offset=0, range=tam)
                escrituras[i] = VkWriteDescriptorSet(
                    sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, pNext=None,
                    dstSet=ctypes.cast(sets, ctypes.c_void_p), dstBinding=i,
                    dstArrayElement=0, descriptorCount=1,
                    descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, pImageInfo=None,
                    pBufferInfo=ctypes.cast(ctypes.byref(infos[i]), ctypes.c_void_p),
                    pTexelBufferView=None)
            vk.vkUpdateDescriptorSets(self.dispositivo, len(creados), escrituras, 0, None)

            empezar = VkCommandBufferBeginInfo(
                sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, pNext=None, flags=0,
                pInheritanceInfo=None)
            vk.vkBeginCommandBuffer(self.cmd, ctypes.byref(empezar))
            vk.vkCmdBindPipeline(self.cmd, VK_PIPELINE_BIND_POINT_COMPUTE, tuberia)
            vk.vkCmdBindDescriptorSets(self.cmd, VK_PIPELINE_BIND_POINT_COMPUTE, layout, 0, 1,
                                       ctypes.byref(sets), 0, None)
            if push:
                cuerpo = ctypes.create_string_buffer(push, len(push))
                vk.vkCmdPushConstants(self.cmd, layout, VK_SHADER_STAGE_COMPUTE_BIT, 0,
                                      len(push), ctypes.cast(cuerpo, ctypes.c_void_p))
            vk.vkCmdDispatch(self.cmd, grupos, 1, 1)

            barrera = VkBufferMemoryBarrier(
                sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER, pNext=None,
                srcAccessMask=0x00000008, dstAccessMask=VK_ACCESS_MEMORY_READ_BIT,
                srcQueueFamilyIndex=0xFFFFFFFF, dstQueueFamilyIndex=0xFFFFFFFF,
                buffer=salida[0], offset=0, size=salida[3])
            vk.vkCmdPipelineBarrier(self.cmd, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                                    VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, None, 1,
                                    ctypes.byref(barrera), 0, None)
            vk.vkEndCommandBuffer(self.cmd)

            enviar = VkSubmitInfo(sType=VK_STRUCTURE_TYPE_SUBMIT_INFO, pNext=None,
                                  waitSemaphoreCount=0, pWaitSemaphores=None,
                                  pWaitDstStageMask=None, commandBufferCount=1,
                                  pCommandBuffers=ctypes.cast(ctypes.byref(self.cmd),
                                                              ctypes.c_void_p),
                                  signalSemaphoreCount=0, pSignalSemaphores=None)
            vk.vkResetFences(self.dispositivo, 1, ctypes.byref(self.fence))
            if vk.vkQueueSubmit(self.cola, 1, ctypes.byref(enviar), self.fence) != VK_SUCCESS:
                raise RuntimeError('vkQueueSubmit')
            vk.vkWaitForFences(self.dispositivo, 1, ctypes.byref(self.fence), 1, 10 ** 10)

            crudo = ctypes.string_at(salida[2], salida_bytes)
            return crudo
        finally:
            pass            # los buffers se quedan en el pozo para la siguiente llamada

    # ----------------------------------------------------------- atajos
    def escalar(self, x, g):
        x = np.ascontiguousarray(x, dtype=np.float32)
        n = x.size
        push = struct.pack('<I', n) + struct.pack('<f', g)
        crudo = self.ejecutar('escalar', [x.tobytes()], n * 4, push, (n + 255) // 256)
        return np.frombuffer(crudo, dtype=np.float32, count=n).reshape(x.shape)

    def mul_por_vector(self, x, gan, canales):
        x = np.ascontiguousarray(x, dtype=np.float32)
        gan = np.ascontiguousarray(gan, dtype=np.float32)
        n = x.size
        push = struct.pack('<I', n) + struct.pack('<I', canales)
        crudo = self.ejecutar('mul_vec', [x.tobytes(), gan.tobytes()], n * 4, push,
                              (n + 255) // 256)
        return np.frombuffer(crudo, dtype=np.float32, count=n).reshape(x.shape)

    def estereo_ms(self, x, gm, gl):
        x = np.ascontiguousarray(x, dtype=np.float32)
        tramas = x.size // 2
        push = (struct.pack('<I', tramas) + struct.pack('<f', gm)
                + struct.pack('<f', gl))
        crudo = self.ejecutar('estereo', [x.tobytes()], x.size * 4, push,
                              (tramas + 127) // 128)
        return np.frombuffer(crudo, dtype=np.float32, count=x.size).reshape(x.shape)

    def saturar(self, x, k):
        x = np.ascontiguousarray(x, dtype=np.float32)
        n = x.size
        push = struct.pack('<I', n) + struct.pack('<f', k)
        crudo = self.ejecutar('saturar', [x.tobytes()], n * 4, push, (n + 255) // 256)
        return np.frombuffer(crudo, dtype=np.float32, count=n).reshape(x.shape)

    def pico_real(self, x, taps, desfases):
        """x (tramas, canales); taps (4, k); desfases [d0..d3] -> envolvente (tramas,)."""
        x = np.ascontiguousarray(x, dtype=np.float32)
        tramas = x.size // x.shape[1] if x.ndim > 1 else x.size
        canales = x.shape[1] if x.ndim > 1 else 1
        taps = np.ascontiguousarray(taps, dtype=np.float32)
        ktaps = taps.shape[1]
        push = (struct.pack('<I', tramas) + struct.pack('<I', canales)
                + struct.pack('<I', ktaps) + struct.pack('<I', 0)
                + b''.join(struct.pack('<I', int(d)) for d in desfases))
        crudo = self.ejecutar('pico_real', [x.tobytes(), taps.tobytes()], tramas * 4, push,
                              (tramas + 127) // 128)
        return np.frombuffer(crudo, dtype=np.float32, count=tramas)


_instancia = None
_probado = False


def motor():
    """Devuelve el contexto Vulkan compartido, o None si no hay driver."""
    global _instancia, _probado
    if not _probado:
        _probado = True
        try:
            v = Vulkan()
            _instancia = v if v.listo else None
        except Exception:
            _instancia = None
    return _instancia


def describe():
    v = motor()
    if v is None:
        return 'Vulkan: no disponible'
    return 'Vulkan: ' + v.nombre


if __name__ == '__main__':
    import time
    v = motor()
    print(describe())
    if v is not None:
        rng = np.random.default_rng(1)
        x = (rng.standard_normal((48000, 2)) * 0.1).astype(np.float32)
        t0 = time.perf_counter()
        y = v.escalar(x, 0.5)
        print('escalar %.1f ms, dif %.2e' % ((time.perf_counter() - t0) * 1000,
                                             float(np.max(np.abs(y - x * 0.5)))))
        t0 = time.perf_counter()
        z = v.estereo_ms(x, 1.2, 0.8)
        m = (x[:, 0] + x[:, 1]) / 2 * 1.2
        s = (x[:, 0] - x[:, 1]) / 2 * 0.8
        ref = np.stack([m + s, m - s], axis=1)
        print('estéreo %.1f ms, dif %.2e' % ((time.perf_counter() - t0) * 1000,
                                             float(np.max(np.abs(z - ref)))))
        t0 = time.perf_counter()
        w = v.saturar(x, 3.0)
        print('saturar %.1f ms, dif %.2e' % ((time.perf_counter() - t0) * 1000,
                                             float(np.max(np.abs(w - np.tanh(x * 3.0))))))
        w2 = v.mul_por_vector(x, np.full(48000, 0.3, dtype=np.float32), 2)
        ref2 = x * np.full(48000, 0.3, dtype=np.float32)[:, None]
        print('mul_vec dif %.2e' % float(np.max(np.abs(w2 - ref2))))
    else:
        print('sin Vulkan:', Vulkan().error if _instancia is None else '')
