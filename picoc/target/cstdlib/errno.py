import errno
from interpreter import *
from variable import VariableModule


class ErrnoModule:
    @staticmethod
    def Setup(pc):
        errno_names = [
            "EACCES", "EADDRINUSE", "EADDRNOTAVAIL", "EAFNOSUPPORT",
            "EAGAIN", "EALREADY", "EBADF", "EBADMSG", "EBUSY", "ECANCELED",
            "ECHILD", "ECONNABORTED", "ECONNREFUSED", "ECONNRESET", "EDEADLK",
            "EDESTADDRREQ", "EDOM", "EDQUOT", "EEXIST", "EFAULT", "EFBIG",
            "EHOSTUNREACH", "EIDRM", "EILSEQ", "EINPROGRESS", "EINTR",
            "EINVAL", "EIO", "EISCONN", "EISDIR", "ELOOP", "EMFILE", "EMLINK",
            "EMSGSIZE", "EMULTIHOP", "ENAMETOOLONG", "ENETDOWN", "ENETRESET",
            "ENETUNREACH", "ENFILE", "ENOBUFS", "ENODATA", "ENODEV", "ENOENT",
            "ENOEXEC", "ENOLCK", "ENOLINK", "ENOMEM", "ENOMSG", "ENOPROTOOPT",
            "ENOSPC", "ENOSR", "ENOSTR", "ENOSYS", "ENOTCONN", "ENOTDIR",
            "ENOTEMPTY", "ENOTRECOVERABLE", "ENOTSOCK", "ENOTSUP", "ENOTTY",
            "ENXIO", "EOPNOTSUPP", "EOVERFLOW", "EOWNERDEAD", "EPERM", "EPIPE",
            "EPROTO", "EPROTONOSUPPORT", "EPROTOTYPE", "ERANGE", "EROFS",
            "ESPIPE", "ESRCH", "ESTALE", "ETIME", "ETIMEDOUT", "ETXTBSY",
            "EWOULDBLOCK", "EXDEV",
        ]
        for name in errno_names:
            val = getattr(errno, name, None)
            if val is not None:
                VariableModule.DefinePlatformVar(pc, None, name, pc.IntType, val, False)
        import ctypes
        errno_val = ctypes.c_int(0)
        VariableModule.DefinePlatformVar(pc, None, "errno", pc.IntType, errno_val, True)
