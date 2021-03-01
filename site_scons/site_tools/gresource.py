import itertools
from pathlib import Path
from typing import Any, List, Optional
import xml.etree.ElementTree as ET

import SCons.Node
import SCons.Node.FS
import SCons.Node.Python
from SCons.Script import Action, Builder, DirScanner, Scanner
import SCons.Util


def exists(env):
    return env.Detect('glib-compile-resources')


def generate(env):
    gcr = env.Detect('glib-compile-resources')
    env.SetDefault(GLIB_COMPILE_RESOURCES=gcr)

    if env['GLIB_COMPILE_RESOURCES'] is None:
        print("Could not find glib-compile-resources")
        env.Exit(1)

    env.AddMethod(gresource_bundle_builder_wrapper, 'GResourceBundle')
    env.AddMethod(gresource_method, 'GResource')

    env['BUILDERS']['_GResourceXMLInternal'] = Builder(
        action=Action(
            gresource_xml_build,
            cmdstr="Generating $TARGET",
        ),
        target_factory=env.File,
        source_factory=GResourceEntry,
        source_scanner=Scanner(
            function=gresource_entry_scan,
            skeys=[GResourceEntry.SCANNER_KEY],
        ),
    )

    env['BUILDERS']['_GResourceFileInternal'] = Builder(
        action=Action(
            '$GLIB_COMPILE_RESOURCES --target=$TARGET $SOURCE',
            cmdstr="Bundling $TARGET",
        ),
        source_scanner=Scanner(
            function=gresource_xml_scan,
        ),
    )


def gresource_bundle_builder_wrapper(env, target, source):
    target = env.arg2nodes(target, node_factory=env.File)
    source = env.arg2nodes(source, node_factory=env.Entry)

    recipe = env._GResourceXMLInternal(str(target[0])+'.xml', source)
    bundle = env._GResourceFileInternal(target[0], recipe)

    env.Clean(bundle, recipe)

    return bundle


def gresource_xml_build(target, source, env):
    xml_tree = ET.ElementTree(ET.Element('gresources'))
    files_root = ET.SubElement(xml_tree.getroot(), 'gresource')

    resource_files = {}

    for res_entry in source:
        respath = Path(res_entry.respath)

        if isinstance(res_entry.source, SCons.Node.FS.Base) and res_entry.source.isdir():
            for child in DirScanner(res_entry.source, env):
                child_respath = respath/Path(child.get_path()).relative_to(res_entry.source.get_path())
                child_res_entry = GResourceEntry(str(child_respath), child, compressed=res_entry.compressed)
                source.append(child_res_entry)

            continue

        resource_files[respath] = (res_entry.source, res_entry.compressed)

    for respath, (res_source, compressed) in resource_files.items():
        attrib = {'alias': str(respath)}

        if compressed:
            attrib['compressed'] = "true"

        ET.SubElement(files_root, 'file', attrib).text = res_source.get_path()

    xml_tree.write(str(target[0]))


def gresource_xml_scan(node, env, path):
    try:
        root = ET.fromstring(node.get_text_contents())
    except ET.ParseError:
        return []

    includes = [elm.text for elm in root.iter(tag='file')]

    # The referenced file paths should be relative to the source directory, not the xml file parent.
    includes = env.File(includes)

    return includes


def gresource_method(
        env,
        prefix,
        source=None,
        *,
        parents: bool = True,
        root: str = '',
        compressed: bool = False
):
    if source is None:
        source = prefix
        prefix = ['']

    if not SCons.Util.is_List(prefix):
        prefix = [prefix]

    source = env.arg2nodes(source, node_factory=env.Entry)

    respaths = [Path(s.get_path()) for s in source]
    if parents:
        respaths = [p.relative_to(root) for p in respaths]

    target = []

    for pre, (respath, res_source) in itertools.product(prefix, zip(respaths, source)):
        respath = str(pre/respath)
        target.append(GResourceEntry(respath, source=res_source, compressed=compressed))

    return target


def gresource_entry_scan(node, env, path):
    if not isinstance(node, GResourceEntry): return []

    source = node.source

    if isinstance(source, SCons.Node.FS.Base) and source.isdir():
        includes = DirScanner(source.disambiguate(), env, path)
    else:
        includes = [source]

    return includes


class GResourceEntry(SCons.Node.Python.Value):
    SCANNER_KEY = object()

    def __init__(
            self,
            respath: str,
            source: Optional[SCons.Node.Node] = None,
            *,
            compressed: bool = False
    ) -> None:
        super().__init__(value=(respath, compressed))
        if source is not None:
            self.set_source(source)

    @property
    def respath(self) -> str:
        return self.value[0]

    @property
    def compressed(self) -> bool:
        return self.value[1]

    def set_source(self, source: SCons.Node.Node) -> None:
        self.write(source)

    @property
    def source(self) -> Optional[SCons.Node.Node]:
        if not self._is_built:
            return None

        return self.read()

    @property
    def _is_built(self) -> bool:
        return hasattr(self, 'built_value')

    def get_found_includes(self, env, scanner, path) -> List[SCons.Node.Node]:
        return scanner(self, env, path)

    def get_text_contents(self) -> str:
        return ' '.join([self.respath, str(self.source), 'compressed={}'.format(self.compressed)])

    def get_contents(self) -> bytes:
        return self.get_text_contents().encode()

    def scanner_key(self) -> Any:
        return GResourceEntry.SCANNER_KEY
