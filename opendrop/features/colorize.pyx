cimport cython
from libc.stdint cimport *
from libc.string cimport memcpy
from cpython cimport array
import array


__all__ = ('colorize_labels',)


ctypedef fused integral:
    int8_t
    uint8_t
    int16_t
    uint16_t
    int32_t
    uint32_t
    int64_t
    uint64_t


@cython.boundscheck(False)
@cython.wraparound(False)
def colorize_labels(integral[:, :] labels not None, uint8_t[:, ::1] colors not None):
    cdef size_t i, j, n
    cdef array.array arr
    cdef uint8_t[:, :, :] view
    
    if colors.shape[1] != 4:
        raise ValueError(
            "axis 1 of colors array must equal 4, got {}"
            .format(colors.shape[1])
        )
    
    arr = array.array('B')
    array.resize(arr, labels.shape[0]*labels.shape[1]*4)
    
    view = <uint8_t[:labels.shape[0], :labels.shape[1], :4]> arr.data.as_uchars

    for i in range(labels.shape[0]):
        for j in range(labels.shape[1]):
            n = labels[i][j]
            
            if n >= colors.shape[0]:
                raise IndexError(
                    "index {} is out of bounds for axis 0 of colors array with shape {}"
                    .format(n, (colors.shape[0], colors.shape[1]))
                )
            
            memcpy(<void *>&view[i][j][0], <void *>&colors[n][0], 4)

    return arr
