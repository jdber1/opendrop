import base64
from collections import defaultdict
import csv
import hashlib
import io
import itertools
from pathlib import Path
from typing import List, Optional, Any, Mapping
import zipfile

from SCons.Script import Action, Builder, DirScanner, Scanner
from SCons.Environment import OverrideEnvironment
import SCons.Node
import SCons.Node.FS
import SCons.Node.Python
import SCons.Util


def exists(env):
    return True


def generate(env):
    env.AddMethod(wheel_package_builder_wrapper, 'WheelPackage')
    env.AddMethod(wheel_method, 'Wheel')

    env['BUILDERS']['_WheelFileInternal'] = Builder(
        action=Action(
            wheel_package_build,
            varlist=[
                'AUTHOR',
                'NAME',
                'VERSION',
                'AUTHOR',
                'AUTHOR_EMAIL',
                'LICENSE',
                'ARCHITECTURE',
                'PACKAGE_METADATA',
                'SOURCE_URL',
                'BUILD',
                '_WHEEL_ROOT_IS_PURELIB',
                '_WHEEL_TAG',
            ],
            cmdstr="Packaging $TARGET",
        ),
        target_factory=env.File,
        source_factory=lambda s: WheelEntry(s, env.Entry(s)),
        source_scanner=Scanner(
            function=wheel_entry_scan,
            skeys=[WheelEntry.SCANNER_KEY],
        ),
    )


def wheel_package_builder_wrapper(
        env,
        target,
        source=None,
        *,
        purelib=(),
        platlib=(),
        scripts=(),
        packages=None,
        root_is_purelib=True,
        python_tag='py3',
        abi_tag='none',
        platform_tag='any',
):
    if source is None:
        source = target
        target = '.'

    env = OverrideEnvironment(env, {
        '_WHEEL_ROOT_IS_PURELIB': root_is_purelib,
        '_WHEEL_TAG': '{}-{}-{}'.format(python_tag, abi_tag, platform_tag),
    })

    wheel_filename = format_wheel_package_filename(**env)

    target = env.arg2nodes(target, node_factory=env.Dir)
    target = target[0].File(wheel_filename)
    
    packages = packages or {}

    source = env.arg2nodes(source, node_factory=env.Entry)
    purelib = env.arg2nodes(purelib, node_factory=env.Entry)
    platlib = env.arg2nodes(platlib, node_factory=env.Entry)
    scripts = env.arg2nodes(scripts, node_factory=env.Entry)
    packages = {name: env.Dir(d) for name, d in packages.items()}

    wheel_entries = []

    for category, nodes in {None: source, 'purelib': purelib, 'platlib': platlib}.items():
        for node in nodes:
            if isinstance(node, WheelEntry):
                if category is not None:
                    raise ValueError(
                        "Cannot use WheelEntry sources with convenience parameters 'purelib' and 'platlib'"
                    )
                wheel_entry = node
            else:
                arcpath = find_package_entry_dest(node, packages)
                wheel_entry = WheelEntry(arcpath, node, category=category)

            wheel_entries.append(wheel_entry)

    for node in scripts:
        wheel_entries.append(WheelEntry(
            arcpath=node.name,
            source=node,
            category='scripts',
        ))

    return env._WheelFileInternal(target, wheel_entries)


def find_package_entry_dest(node: SCons.Node.FS.Entry, packages: Mapping[str, SCons.Node.FS.Dir]) -> str:
    node_path = Path(node.get_path())
    dest_path = node_path

    for package_name, package_dir in packages.items():
        package_dir_path = Path(package_dir.get_path())
        if package_dir_path == node_path or package_dir_path in node_path.parents:
            dest_path = package_name/node_path.relative_to(package_dir_path)
            break
        elif node_path in package_dir_path.parents:
            raise RuntimeError(
                "Package directory '{!s}' refers to a location within source node '{!s}'"
                .format(package_dir_path, node_path)
            )

    return str(dest_path)


def format_wheel_package_filename(**kw):
    pkg_metadata = PackageMetadata(**kw)
    wheel_metadata = WheelMetadata(**kw)

    filename = '{name}-{version}'.format(name=pkg_metadata['Name'], version=pkg_metadata['Version'])

    if wheel_metadata['Build']:
        filename += '-{build}'.format(build=wheel_metadata['Build'])

    filename += '-{tag}'.format(tag=wheel_metadata['Tag'])
    filename += '.whl'

    return filename


def wheel_package_build(target, source, env):
    if not all(isinstance(s, WheelEntry) for s in source):
        raise ValueError("Sources of WheelPackage must be WheelEntry nodes")

    pkg_metadata = PackageMetadata(**env)
    wheel_metadata = WheelMetadata(**env)

    dist_info_prefix = Path('{0[Name]}-{0[Version]}.dist-info'.format(pkg_metadata))
    data_prefix = Path('{0[Name]}-{0[Version]}.data'.format(pkg_metadata))

    archive = {}

    for wheel_entry in source:
        arcpath = Path(wheel_entry.arcpath)

        if isinstance(wheel_entry.source, SCons.Node.FS.Base) and wheel_entry.source.isdir():
            for child in DirScanner(wheel_entry.source.disambiguate(), env):
                child_arcpath = arcpath/Path(child.get_path()).relative_to(wheel_entry.source.get_path())
                child_wheel_entry = WheelEntry(str(child_arcpath), child, category=wheel_entry.category)
                source.append(child_wheel_entry)

            continue

        if wheel_entry.category:
            arcpath = data_prefix/wheel_entry.category/arcpath

        archive[arcpath] = wheel_entry.source

    archive[dist_info_prefix/'METADATA'] = str(pkg_metadata).encode()
    archive[dist_info_prefix/'WHEEL'] = str(wheel_metadata).encode()

    record_io = io.StringIO()
    record_writer = csv.writer(record_io, delimiter=',', quotechar='"', lineterminator='\n')

    with zipfile.ZipFile(str(target[0]), mode='w') as wheel:
        for arcpath, content in archive.items():
            if isinstance(content, bytes):
                digest, size = zip_writebytes(wheel, arcpath, content)
            elif isinstance(content, SCons.Node.Node):
                digest, size = zip_writebytes(wheel, arcpath, content.get_contents())
            else:
                raise RuntimeError

            record_writer.writerow([
                str(arcpath),
                'sha256={}'.format(format_digest(digest)),
                str(size),
            ])

        record_arcpath = str(dist_info_prefix/'RECORD')
        record_writer.writerow([record_arcpath, '', ''])

        wheel.writestr(record_arcpath, record_io.getvalue())


def zip_writebytes(zip_file, arcpath, content):
    zip_file.writestr(str(arcpath), content)
    hash_digest = hashlib.sha256(content).digest()
    size = len(content)
    return hash_digest, size


def format_digest(digest: bytes) -> str:
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def wheel_method(env, prefix, source=None, *, parents=True, root='', category=None):
    if source is None:
        source = prefix
        prefix = ['']

    if not SCons.Util.is_List(prefix):
        prefix = [prefix]

    source = env.arg2nodes(source, node_factory=env.Entry)

    arcpaths = [Path(s.get_path()) for s in source]
    if parents:
        arcpaths = [p.relative_to(root) for p in arcpaths]

    target = []

    for pre, (arcpath, s) in itertools.product(prefix, zip(arcpaths, source)):
        arcpath = str(pre/arcpath)
        target.append(WheelEntry(arcpath, source=s, category=category))

    return target


def wheel_entry_scan(node, env, path):
    if not isinstance(node, WheelEntry): return []

    source = node.source

    if isinstance(source, SCons.Node.FS.Base) and source.isdir():
        includes = DirScanner(source.disambiguate(), env, path)
    else:
        includes = [source]

    return includes


class WheelEntry(SCons.Node.Python.Value):
    SCANNER_KEY = object()

    def __init__(
            self,
            arcpath: str,
            source: Optional[SCons.Node.Node] = None,
            *,
            category: Optional[str] = None
    ) -> None:
        super().__init__(value=(arcpath, category))
        if source is not None:
            self.set_source(source)

    @property
    def _is_built(self) -> bool:
        return hasattr(self, 'built_value')

    def set_source(self, source: SCons.Node.Node) -> None:
        self.write(source)

    @property
    def arcpath(self) -> str:
        return self.value[0]

    @property
    def category(self) -> Optional[str]:
        return self.value[1]

    @property
    def source(self) -> Optional[SCons.Node.Node]:
        if not self._is_built:
            return None

        return self.read()

    def get_found_includes(self, env, scanner, path) -> List[SCons.Node.Node]:
        return scanner(self, env, path)

    def get_text_contents(self) -> str:
        return ' '.join([self.category or 'root', self.arcpath, str(self.source)])

    def get_contents(self) -> bytes:
        return self.get_text_contents().encode()

    def scanner_key(self) -> Any:
        return WheelEntry.SCANNER_KEY


class PackageMetadata:
    __metadata_version = '2.1'

    def __init__(self, **kw) -> None:
        self.__metadata = defaultdict(type(None))

        self.__metadata['Metadata-Version'] = self.__metadata_version

        if 'NAME' in kw:
            self.__metadata['Name'] = kw['NAME']
        if 'VERSION' in kw:
            self.__metadata['Version'] = kw['VERSION']
        if 'AUTHOR' in kw:
            self.__metadata['Author'] = kw['AUTHOR']
        if 'AUTHOR_EMAIL' in kw:
            self.__metadata['Author-email'] = kw['AUTHOR_EMAIL']
        if 'LICENSE' in kw:
            self.__metadata['License'] = kw['LICENSE']
        if 'ARCHITECTURE' in kw:
            self.__metadata['Supported-Platform'] = kw['ARCHITECTURE']
        if 'PACKAGE_METADATA' in kw:
            self.__metadata.update(kw['PACKAGE_METADATA'])

        if 'Name' not in self.__metadata:
            raise ValueError("'Name' field required")
        if 'Version' not in self.__metadata:
            raise ValueError("'Version' field required")

    def __str__(self) -> str:
        ret = (
            "Metadata-Version: {self[Metadata-Version]}\n"
            "Name: {self[Name]}\n"
            "Version: {self[Version]}\n"
            .format(self=self)
        )

        items = []

        for name, value in self.__metadata.items():
            if name in ('Metadata-Version', 'Name', 'Version'): continue

            if isinstance(value, (list, tuple, set)):
                for value in value:
                    items.append((name, value))
            else:
                items.append((name, value))

        for name, value in items:
            if isinstance(value, bool):
                value = str(value).lower()
            ret += '{}: {}\n'.format(name, value)

        return ret

    def __getitem__(self, name: str) -> Any:
        return self.__metadata[name]


class SDistMetadata(PackageMetadata):
    def __init__(self, **kw):
        package_metadata = {}

        if 'SOURCE_URL' in kw:
            package_metadata['Download-URL'] = kw['SOURCE_URL']

        if 'PACKAGE_METADATA' in kw:
            package_metadata.update(kw['PACKAGE_METADATA'])

        kw['PACKAGE_METADATA'] = package_metadata

        super().__init__(**kw)


class WheelMetadata:
    __wheel_version = '1.0'
    __generator = 'opendrop'

    def __init__(self, **kw):
        self.__metadata = defaultdict(type(None))

        self.__metadata['Wheel-Version'] = self.__wheel_version
        self.__metadata['Generator'] = self.__generator

        # Default values.
        self.__metadata['Root-Is-Purelib'] = True
        self.__metadata['Tag'] = 'py3-none-any'

        if 'BUILD' in kw:
            self.__metadata['Build'] = kw['BUILD']
        if '_WHEEL_ROOT_IS_PURELIB' in kw:
            self.__metadata['Root-Is-Purelib'] = kw['_WHEEL_ROOT_IS_PURELIB']
        if '_WHEEL_TAG' in kw:
            self.__metadata['Tag'] = kw['_WHEEL_TAG']

    def __str__(self) -> str:
        ret = 'Wheel-Version: {}\n'.format(self['Wheel-Version'])
        ret += 'Generator: {}\n'.format(self['Generator'])
        ret += "Root-Is-Purelib: {}\n".format(str(self['Root-Is-Purelib']).lower())
        ret += "Tag: {}\n".format(self['Tag'])

        if self['Build'] is not None:
            ret += "Build: {}\n".format(self['Build'])

        return ret

    def __getitem__(self, name: str) -> Optional[str]:
        return self.__metadata[name]
