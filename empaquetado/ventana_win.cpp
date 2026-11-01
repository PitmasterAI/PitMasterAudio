/* Ventana propia de PitMasterAudio para Windows: WebView2 embebido.
 *
 * Igual que la ventana del AppImage (GTK+WebKit): una ventana de la aplicacion con el
 * panel dentro, sin navegador y sin barras. Usa el motor WebView2 (Edge incrustado),
 * que viene con Windows 10/11.
 *
 * Uso:  ventana.exe <url> [--datos CARPETA]
 * Si no hay WebView2 responde con codigo 2 para que el lanzador haga su plan B.
 */
#define _UNICODE
#include <windows.h>
#include <objbase.h>
#include <cstdio>
#include "WebView2.h"

static ICoreWebView2Controller *g_control = nullptr;

/* mingw no resuelve __uuidof sobre interfaces MIDL: los IID van a mano */
static const GUID IID_Entorno =
    {0x4e8a3389, 0xc9d8, 0x4bd2, {0xb6, 0xb5, 0x12, 0x4f, 0xee, 0x6c, 0xc1, 0x4d}};
static const GUID IID_Control =
    {0x6c4819f3, 0xc9b7, 0x4260, {0x81, 0x27, 0xc9, 0xf5, 0xbd, 0xe7, 0xf6, 0x8c}};
static const GUID IID_VentanaNueva =
    {0xd4c185fe, 0xc81c, 0x4989, {0x97, 0xaf, 0x3c, 0x5a, 0x42, 0x26, 0xdb, 0x8c}};
static HWND g_ventana = nullptr;
static wchar_t g_url[1024] = L"http://127.0.0.1:5077/";
static wchar_t g_datos[MAX_PATH] = L"";

static void ajustar(void)
{
    if (!g_control) return;
    RECT r;
    GetClientRect(g_ventana, &r);
    g_control->put_Bounds(r);
}

/* Un enlace con target=_blank (el boton de Donar, la web…) se abre en el navegador
 * del sistema: dentro de esta ventana no hay pestanas y WebView2 lo dejaria en nada. */
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

/* ---- manejadores COM sin WRL (minGW no trae wrl/client.h) ------------------ */
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
        PostQuitMessage(2);        /* sin WebView2: el lanzador decide */
        return S_OK;
    }
    entorno->CreateCoreWebView2Controller(g_ventana, new ManoControl());
    return S_OK;
}

/* ---- ventana --------------------------------------------------------------- */
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

    /* WebView2Loader.dll junto al programa */
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
