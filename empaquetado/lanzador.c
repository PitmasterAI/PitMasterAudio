#define _UNICODE
#include <windows.h>
#include <shellapi.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#define PUERTO_TXT L"5077"
#define URL        L"http://127.0.0.1:5077/"
#ifndef MAX_RUTA
#define MAX_RUTA 1024
#endif

static PROCESS_INFORMATION py;
static wchar_t carpeta[MAX_RUTA];
static wchar_t fichero_log[MAX_RUTA];

static void anotar(const wchar_t *texto)
{
    HANDLE f = CreateFileW(fichero_log, FILE_APPEND_DATA, FILE_SHARE_READ, NULL,
                           OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    DWORD escrito = 0;
    WriteFile(f, texto, (DWORD)(lstrlenW(texto) * sizeof(wchar_t)), &escrito, NULL);
    WriteFile(f, L"\r\n", 4, &escrito, NULL);
    CloseHandle(f);
}

static void unir(wchar_t *destino, const wchar_t *a, const wchar_t *b)
{
    lstrcpynW(destino, a, MAX_RUTA);
    lstrcatW(destino, b);
}

static int panel_responde(void)
{
    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    int listo = 0;
    if (s != INVALID_SOCKET) {
        struct sockaddr_in dir;
        ZeroMemory(&dir, sizeof(dir));
        dir.sin_family = AF_INET;
        dir.sin_port = htons(5077);
        dir.sin_addr.s_addr = inet_addr("127.0.0.1");
        if (connect(s, (struct sockaddr *)&dir, sizeof(dir)) == 0) listo = 1;
        closesocket(s);
    }
    return listo;
}

static void asegurar_preguntar_descargas(const wchar_t *perfil)
{
    wchar_t carpeta_defecto[MAX_RUTA],preferencias[MAX_RUTA];
    static const char json[] = "{\"download\":{\"prompt_for_download\":true}}";
    HANDLE f;
    DWORD escrito = 0;

    unir(carpeta_defecto, perfil, L"\\Default");
    CreateDirectoryW(perfil, NULL);
    CreateDirectoryW(carpeta_defecto, NULL);
    unir(preferencias, carpeta_defecto, L"\\Preferences");
    if (GetFileAttributesW(preferencias) != INVALID_FILE_ATTRIBUTES) return;
    f = CreateFileW(preferencias, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS,
                    FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    WriteFile(f, json, (DWORD)(sizeof(json) - 1), &escrito, NULL);
    CloseHandle(f);
}

static int lanzar(const wchar_t *exe, const wchar_t *argumentos,
                  DWORD banderas, PROCESS_INFORMATION *pi)
{
    wchar_t linea[4096];
    lstrcpynW(linea, L"\"", 4096);
    lstrcatW(linea, exe);
    lstrcatW(linea, L"\"");
    if (argumentos && *argumentos) {
        lstrcatW(linea, L" ");
        lstrcatW(linea, argumentos);
    }

    STARTUPINFOW si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);

    wchar_t ruta_log[MAX_RUTA];
    unir(ruta_log, carpeta, L"\\datos\\panel.log");
    HANDLE f = CreateFileW(ruta_log, FILE_APPEND_DATA,
                           FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                           OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
        SetFilePointer(f, 0, NULL, FILE_END);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdOutput = f;
        si.hStdError = f;
        si.hStdInput = INVALID_HANDLE_VALUE;
        banderas |= CREATE_NO_WINDOW;
    }
    BOOL bien = CreateProcessW(exe, linea, NULL, NULL, f != INVALID_HANDLE_VALUE,
                               banderas, NULL, carpeta, &si, pi);
    if (f != INVALID_HANDLE_VALUE) CloseHandle(f);
    return bien ? 1 : 0;
}

static HANDLE g_job = NULL;

static void crear_job(void)
{
    g_job = CreateJobObjectW(NULL, NULL);
    if (!g_job) return;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION info;
    ZeroMemory(&info, sizeof(info));
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    SetInformationJobObject(g_job, JobObjectExtendedLimitInformation, &info, sizeof(info));
}

static void cerrar_todo(void)
{
    if (py.hProcess) {
        TerminateProcess(py.hProcess, 0);
        WaitForSingleObject(py.hProcess, 3000);
        CloseHandle(py.hProcess);
        CloseHandle(py.hThread);
        py.hProcess = NULL;
    }
    if (g_job) {
                CloseHandle(g_job);
        g_job = NULL;
    }
}

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrev, PWSTR cmd, int mostrar)
{
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

        GetModuleFileNameW(NULL, carpeta, MAX_RUTA);
    {
        wchar_t *barra = wcsrchr(carpeta, L'\\');
        if (barra) *barra = L'\0';
    }
    unir(fichero_log, carpeta, L"\\datos\\lanzador.log");
    CreateDirectoryW((unir((wchar_t[MAX_RUTA]){0}, carpeta, L"\\datos"), L""), NULL);

    anotar(L"--- arranque");
    anotar(carpeta);

        SetEnvironmentVariableW(L"PUERTO", PUERTO_TXT);
    SetEnvironmentVariableW(L"HOST", L"127.0.0.1");
    {
        wchar_t datos[MAX_RUTA];
        unir(datos, carpeta, L"\\datos");
        SetEnvironmentVariableW(L"MASTERLAB_DATA", datos);
    }

    wchar_t python[MAX_RUTA];
    unir(python, carpeta, L"\\python\\python.exe");
    if (GetFileAttributesW(python) == INVALID_FILE_ATTRIBUTES) {
        anotar(L"ERROR: no hay python\\python.exe");
        MessageBoxW(NULL, L"No se encuentra python\\python.exe junto a este programa.",
                    L"PitMasterAudio", MB_ICONERROR);
        return 1;
    }

        {
        wchar_t app[MAX_RUTA];
        unir(app, carpeta, L"\\app\\app.py");
        anotar(L"arrancando el panel");
        crear_job();
        if (!lanzar(python, L"\"app\\app.py\"", CREATE_NO_WINDOW, &py)) {
            anotar(L"ERROR: no se pudo arrancar python");
            MessageBoxW(NULL, L"No se pudo arrancar el servidor del panel.",
                        L"PitMasterAudio", MB_ICONERROR);
            return 1;
        }
        if (g_job) AssignProcessToJobObject(g_job, py.hProcess);
    }

        {
        int listo = 0;
        for (int i = 0; i < 600; i++) {
            if (panel_responde()) { listo = 1; break; }
            Sleep(100);
        }
        anotar(listo ? L"panel respondiendo" : L"AVISO: el panel no respondio a tiempo");
    }

        {
        int cerrada = 0;
        wchar_t ventana[MAX_RUTA];
        unir(ventana, carpeta, L"\\ventana.exe");

        if (GetFileAttributesW(ventana) != INVALID_FILE_ATTRIBUTES) {
            wchar_t datos_web[MAX_RUTA], argumentos[2048];
            unir(datos_web, carpeta, L"\\datos\\webview2");
            lstrcpynW(argumentos, L"\"" URL L"\" --datos \"", 2048);
            lstrcatW(argumentos, datos_web);
            lstrcatW(argumentos, L"\"");

            PROCESS_INFORMATION nav;
            ZeroMemory(&nav, sizeof(nav));
            if (lanzar(ventana, argumentos, 0, &nav)) {
                DWORD arranque = GetTickCount();
                anotar(L"ventana propia abierta; esperando a que se cierre");
                WaitForSingleObject(nav.hProcess, INFINITE);
                DWORD codigo = 0, vivida = GetTickCount() - arranque;
                GetExitCodeProcess(nav.hProcess, &codigo);
                CloseHandle(nav.hProcess);
                CloseHandle(nav.hThread);
                                if (codigo != 2 && codigo != 3 && vivida > 3000) {
                    cerrada = 1;
                } else {
                    anotar(L"sin WebView2 en este equipo: se prueba el navegador");
                }
            }
        }

        if (!cerrada) {
                        wchar_t perfil[MAX_RUTA], argumentos[4096];
            unir(perfil, carpeta, L"\\datos\\navegador");
            asegurar_preguntar_descargas(perfil);
            lstrcpynW(argumentos, L"--app=" URL L" --window-size=1180,900 "
                      L"--autoplay-policy=no-user-gesture-required --user-data-dir=\"", 4096);
            lstrcatW(argumentos, perfil);
            lstrcatW(argumentos, L"\"");

            const wchar_t *candidatos[] = {
                L"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                L"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                L"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                L"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                L"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                L"msedge.exe", L"chrome.exe", L"brave.exe",
            };
            int abierto = 0;
            for (int i = 0; i < (int)(sizeof(candidatos) / sizeof(candidatos[0])); i++) {
                PROCESS_INFORMATION nav;
                ZeroMemory(&nav, sizeof(nav));
                if (lanzar(candidatos[i], argumentos, 0, &nav)) {
                    anotar(L"navegador en modo aplicacion abierto; esperando a que se cierre");
                    WaitForSingleObject(nav.hProcess, INFINITE);
                    CloseHandle(nav.hProcess);
                    CloseHandle(nav.hThread);
                    abierto = 1;
                    break;
                }
            }

            if (!abierto) {
                PROCESS_INFORMATION nav;
                ZeroMemory(&nav, sizeof(nav));
                if (lanzar(L"firefox.exe", L"-new-window " URL, 0, &nav)) {
                    anotar(L"firefox abierto; esperando a que se cierre");
                    WaitForSingleObject(nav.hProcess, INFINITE);
                    CloseHandle(nav.hProcess);
                    CloseHandle(nav.hThread);
                    abierto = 1;
                }
            }

            if (!abierto) {
                anotar(L"sin navegador conocido: se abre con el del sistema y se avisa");
                ShellExecuteW(NULL, L"open", URL, NULL, NULL, SW_SHOWNORMAL);
                MessageBoxW(NULL, L"PitMasterAudio esta en:\n\n" URL
                            L"\n\nCierra esta ventana para parar el programa.",
                            L"PitMasterAudio", MB_OK | MB_ICONINFORMATION);
            }
        }
    }

        anotar(L"cerrando: se para el panel");
    cerrar_todo();
    anotar(L"--- fin");
    WSACleanup();
    return 0;
}
