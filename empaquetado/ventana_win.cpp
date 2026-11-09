#define _UNICODE
#include <windows.h>
#include <objbase.h>
#include <commdlg.h>
#include <cstdio>
#include "WebView2.h"

static ICoreWebView2Controller *g_control = nullptr;

static const GUID IID_Entorno =
    {0x4e8a3389, 0xc9d8, 0x4bd2, {0xb6, 0xb5, 0x12, 0x4f, 0xee, 0x6c, 0xc1, 0x4d}};
static const GUID IID_Control =
    {0x6c4819f3, 0xc9b7, 0x4260, {0x81, 0x27, 0xc9, 0xf5, 0xbd, 0xe7, 0xf6, 0x8c}};
static const GUID IID_VentanaNueva =
    {0xd4c185fe, 0xc81c, 0x4989, {0x97, 0xaf, 0x3c, 0x5a, 0x42, 0x26, 0xdb, 0x8c}};
static const GUID IID_Web4 =
    {0x20d02d59, 0x6df2, 0x42dc, {0xbd, 0x06, 0xf9, 0x8a, 0x69, 0x4b, 0x13, 0x02}};
static const GUID IID_ManoDescarga =
    {0xefedc989, 0xc396, 0x41ca, {0x83, 0xf7, 0x07, 0xf8, 0x45, 0xa5, 0x57, 0x24}};
static HWND g_ventana = nullptr;
static wchar_t g_url[1024] = L"http://127.0.0.1:5077/";
static wchar_t g_datos[MAX_PATH] = L"";
static wchar_t g_guardar_en[MAX_PATH] = L"";

static void nombre_de_ruta(const wchar_t *ruta, wchar_t *nombre, int tam)
{
    const wchar_t *barra;
    if (nombre && tam > 0) nombre[0] = 0;
    if (!ruta || !nombre || tam <= 0) return;
    barra = wcsrchr(ruta, L'\\');
    if (!barra) barra = wcsrchr(ruta, L'/');
    lstrcpynW(nombre, barra ? barra + 1 : ruta, tam);
}

static void ajustar(void)
{
    if (!g_control) return;
    RECT r;
    GetClientRect(g_ventana, &r);
    g_control->put_Bounds(r);
}

class ManoVentanaNueva : public ICoreWebView2NewWindowRequestedEventHandler {
    ULONG ref = 1;
public:
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void **salida) override
    {
        if (!salida) return E_POINTER;
        if (IsEqualIID(iid, IID_IUnknown) || IsEqualIID(iid, IID_VentanaNueva)) {
            *salida = this;
            AddRef();
            return S_OK;
        }
        *salida = nullptr;
        return E_NOINTERFACE;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++ref; }
    ULONG STDMETHODCALLTYPE Release() override
    {
        if (--ref == 0) { delete this; return 0; }
        return ref;
    }
    HRESULT STDMETHODCALLTYPE Invoke(ICoreWebView2 *remitente,
                                     ICoreWebView2NewWindowRequestedEventArgs *args) override
    {
        (void)remitente;
        if (!args) return S_OK;
        LPWSTR destino = nullptr;
        if (SUCCEEDED(args->get_Uri(&destino)) && destino) {
            ShellExecuteW(nullptr, L"open", destino, nullptr, nullptr, SW_SHOWNORMAL);
            CoTaskMemFree(destino);
        }
        args->put_Handled(TRUE);
        return S_OK;
    }
};

class ManoDescarga : public ICoreWebView2DownloadStartingEventHandler {
    ULONG ref = 1;
public:
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void **salida) override
    {
        if (!salida) return E_POINTER;
        if (IsEqualIID(iid, IID_IUnknown) || IsEqualIID(iid, IID_ManoDescarga)) {
            *salida = this;
            AddRef();
            return S_OK;
        }
        *salida = nullptr;
        return E_NOINTERFACE;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++ref; }
    ULONG STDMETHODCALLTYPE Release() override
    {
        if (--ref == 0) { delete this; return 0; }
        return ref;
    }
    HRESULT STDMETHODCALLTYPE Invoke(ICoreWebView2 *remitente,
                                     ICoreWebView2DownloadStartingEventArgs *args) override
    {
        (void)remitente;
        if (!args) return S_OK;

        wchar_t nombre[MAX_PATH] = L"";
        wchar_t ruta[MAX_PATH * 2] = L"";
        wchar_t propuesta[MAX_PATH * 2] = L"";
        LPWSTR porDefecto = nullptr;
        if (SUCCEEDED(args->get_ResultFilePath(&porDefecto)) && porDefecto) {
            lstrcpynW(propuesta, porDefecto, MAX_PATH * 2);
            CoTaskMemFree(porDefecto);
        }
        nombre_de_ruta(propuesta, nombre, MAX_PATH);
        if (!nombre[0]) lstrcpynW(nombre, L"masterizado.wav", MAX_PATH);

        if (g_guardar_en[0]) {
                        wsprintfW(ruta, L"%s\\%s", g_guardar_en, nombre);
            args->put_ResultFilePath(ruta);
            args->put_Handled(TRUE);
            return S_OK;
        }

                if (propuesta[0]) {
            lstrcpynW(ruta, propuesta, MAX_PATH * 2);
        } else {
            lstrcpynW(ruta, nombre, MAX_PATH * 2);
        }

        OPENFILENAMEW dialogo;
        ZeroMemory(&dialogo, sizeof(dialogo));
        dialogo.lStructSize = sizeof(dialogo);
        dialogo.hwndOwner = g_ventana;
        dialogo.lpstrFilter =
            L"Audio\0*.wav;*.mp3;*.flac;*.ogg;*.m4a;*.aiff\0Todos los archivos\0*.*\0\0";
        dialogo.nFilterIndex = 1;
        dialogo.lpstrFile = ruta;
        dialogo.nMaxFile = MAX_PATH * 2;
        dialogo.lpstrDefExt = L"wav";
        dialogo.lpstrTitle = L"Guardar la version masterizada";
        dialogo.Flags = OFN_EXPLORER | OFN_OVERWRITEPROMPT | OFN_PATHMUSTEXIST
            | OFN_NOCHANGEDIR;

        if (GetSaveFileNameW(&dialogo)) {
            args->put_ResultFilePath(ruta);
            args->put_Handled(TRUE);
        } else {
                        args->put_Cancel(TRUE);
            args->put_Handled(TRUE);
        }
        return S_OK;
    }
};

class ManoEntorno : public ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler {
    ULONG ref = 1;
public:
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void **salida) override
    {
        if (!salida) return E_POINTER;
        if (IsEqualIID(iid, IID_IUnknown) || IsEqualIID(iid, IID_Entorno)) {
            *salida = this;
            AddRef();
            return S_OK;
        }
        *salida = nullptr;
        return E_NOINTERFACE;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++ref; }
    ULONG STDMETHODCALLTYPE Release() override
    {
        if (--ref == 0) { delete this; return 0; }
        return ref;
    }
    HRESULT STDMETHODCALLTYPE Invoke(HRESULT resultado,
                                     ICoreWebView2Environment *entorno) override;
};

class ManoControl : public ICoreWebView2CreateCoreWebView2ControllerCompletedHandler {
    ULONG ref = 1;
public:
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void **salida) override
    {
        if (!salida) return E_POINTER;
        if (IsEqualIID(iid, IID_IUnknown) || IsEqualIID(iid, IID_Control)) {
            *salida = this;
            AddRef();
            return S_OK;
        }
        *salida = nullptr;
        return E_NOINTERFACE;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++ref; }
    ULONG STDMETHODCALLTYPE Release() override
    {
        if (--ref == 0) { delete this; return 0; }
        return ref;
    }
    HRESULT STDMETHODCALLTYPE Invoke(HRESULT resultado, ICoreWebView2Controller *control) override
    {
        if (FAILED(resultado) || !control) {
            PostQuitMessage(3);
            return S_OK;
        }
        g_control = control;
        g_control->AddRef();
        ajustar();
        ICoreWebView2 *web = nullptr;
        if (SUCCEEDED(g_control->get_CoreWebView2(&web)) && web) {
            EventRegistrationToken token;
            web->add_NewWindowRequested(new ManoVentanaNueva(), &token);
                        ICoreWebView2_4 *web4 = nullptr;
            if (SUCCEEDED(web->QueryInterface(IID_Web4, (void **)&web4)) && web4) {
                EventRegistrationToken tokenDescarga;
                web4->add_DownloadStarting(new ManoDescarga(), &tokenDescarga);
                web4->Release();
            }
            web->Navigate(g_url);
            web->Release();
        }
        return S_OK;
    }
};

HRESULT STDMETHODCALLTYPE ManoEntorno::Invoke(HRESULT resultado,
                                              ICoreWebView2Environment *entorno)
{
    if (FAILED(resultado) || !entorno) {
        PostQuitMessage(2);         
        return S_OK;
    }
    entorno->CreateCoreWebView2Controller(g_ventana, new ManoControl());
    return S_OK;
}

static LRESULT CALLBACK Procedimiento(HWND v, UINT m, WPARAM w, LPARAM l)
{
    switch (m) {
    case WM_SIZE:
        ajustar();
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(v, m, w, l);
    }
}

int WINAPI wWinMain(HINSTANCE inst, HINSTANCE prev, PWSTR linea, int mostrar)
{
    int argc = 0;
    LPWSTR *args = CommandLineToArgvW(GetCommandLineW(), &argc);
    for (int i = 1; i < argc; i++) {
        if (lstrcmpiW(args[i], L"--datos") == 0 && i + 1 < argc) {
            lstrcpynW(g_datos, args[i + 1], MAX_PATH);
            i++;
        } else if (wcsncmp(args[i], L"http", 4) == 0) {
            lstrcpynW(g_url, args[i], 1024);
        }
    }

    CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

    DWORD tamano = GetEnvironmentVariableW(L"PITMA_GUARDAR_EN", g_guardar_en, MAX_PATH);
    if (tamano == 0 || tamano >= MAX_PATH) g_guardar_en[0] = 0;

    WNDCLASSEXW clase = {0};
    clase.cbSize = sizeof(clase);
    clase.lpfnWndProc = Procedimiento;
    clase.hInstance = inst;
    clase.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    clase.lpszClassName = L"PitMasterAudioVentana";
    RegisterClassExW(&clase);

    g_ventana = CreateWindowExW(0, clase.lpszClassName, L"PitMasterAudio",
                                WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
                                1180, 900, nullptr, nullptr, inst, nullptr);
    if (!g_ventana) return 4;

        HMODULE cargador = LoadLibraryW(L"WebView2Loader.dll");
    if (!cargador) return 2;
    typedef HRESULT (STDAPICALLTYPE *Crear)(PCWSTR, PCWSTR,
                                            ICoreWebView2EnvironmentOptions *,
                                            ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler *);
    Crear crear = (Crear)GetProcAddress(cargador, "CreateCoreWebView2EnvironmentWithOptions");
    if (!crear) {
        FreeLibrary(cargador);
        return 2;
    }

    ShowWindow(g_ventana, mostrar);
    UpdateWindow(g_ventana);

    HRESULT r = crear(nullptr, g_datos[0] ? g_datos : nullptr, nullptr, new ManoEntorno());
    if (FAILED(r)) {
        FreeLibrary(cargador);
        return 2;
    }

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
        if (msg.message == WM_QUIT && (msg.wParam == 2 || msg.wParam == 3)) {
            FreeLibrary(cargador);
            return 2;
        }
    }
    FreeLibrary(cargador);
    return 0;
}
