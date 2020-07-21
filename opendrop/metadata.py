try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata


__all__ = ('__version__',)


try:
    __version__ = importlib_metadata.version(__package__)
except importlib_metadata.PackageNotFoundError:
    __version__ = ''
