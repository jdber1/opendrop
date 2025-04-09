GenICam integration
===================

Install a GenTL producer, (e.g. see `harvesters README <https://github.com/genicam/harvesters#installing-a-gentl-producer>`_).

OpenDrop checks the environment variable GENICAM_GENTL64_PATH (specified by the GenTL standard) for GenTL producers. To verify that a GenTL producer is installed correctly, you can run::

    $ echo $GENICAM_GENTL64_PATH
    /opt/mvIMPACT_Acquire/lib/x86_64

(todo: Add details.)
