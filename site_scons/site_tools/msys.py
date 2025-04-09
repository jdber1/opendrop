import ctypes
import sys


if sys.platform != "msys":
    def native_path(path: str) -> str:
        return path
else:
    msys = ctypes.cdll.LoadLibrary("msys-2.0.dll")
    msys_create_path = msys.cygwin_create_path
    msys_create_path.restype = ctypes.c_void_p
    msys_create_path.argtypes = [ctypes.c_int32, ctypes.c_void_p]

    free = msys.free
    free.restype = None
    free.argtypes = [ctypes.c_void_p]

    CCP_POSIX_TO_WIN_A = 0
    CCP_POSIX_TO_WIN_W = 1
    CCP_WIN_A_TO_POSIX = 2
    CCP_WIN_W_TO_POSIX = 3

    def native_path(path: str) -> str:
        """Convert a Windows path to a msys path"""
        result = msys_create_path(CCP_WIN_W_TO_POSIX, path)
        if result is None:
            raise Exception("msys_create_path failed")
        value = ctypes.cast(result, ctypes.c_char_p).value
        free(result)
        return value.decode()