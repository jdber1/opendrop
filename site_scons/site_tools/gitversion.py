# Generate a project version from git tag names.

import datetime
import os
import re
import subprocess
from typing import NamedTuple


# SemVer regex pattern from https://semver.org
semver_pattern = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


class SemVer(NamedTuple):
    major: int = 0
    minor: int = 0
    patch: int = 0
    pre: str = ''
    build: str = ''

    def __str__(self):
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            text += f".{self.pre}"
        if self.build:
            text += f"+{self.build}"
        return text


def exists(env):
    return env.Detect('git')


def generate(env):
    git = os.environ.get('GIT', None) or env.Detect('git')

    # Fallback git describe output.
    describe_output = 'v0.0.0-0-gdeadbee-dirty'

    if git is not None:
        try:
            describe_output = subprocess.check_output([
                git, 'describe', '--dirty', '--tags', '--long', '--match', "*[0-9]*"
            ]).decode().strip()
        except subprocess.CalledProcessError:
            print("git describe failed, using version number 0.0.0")

    tag, semver, distance, node, dirty = parse_describe(describe_output)

    if semver.build:
        print(f"Ignoring build metadata '{semver.build}' in tag '{tag}'.")
        semver = semver._replace(build='')

    # "Increment" the last version (generate a semver with higher precedence).
    if semver.pre:
        semver = semver._replace(pre=semver.pre + f'.dev{distance}')
    elif distance > 0:
        semver = semver._replace(patch=semver.patch + 1, pre=f'dev{distance}')

    # Add commit abbreviation if there are commits beyond the last tag.
    if distance > 0:
        semver = semver._replace(build=node)

    # Add date if working tree is dirty.
    if dirty:
        date = datetime.datetime.today().strftime('%Y%m%d')
        semver = semver._replace(build=f'{node}.d{date}')

    env['VERSION'] = str(semver)


def parse_describe(output):
    if output.endswith('-dirty'):
        dirty = True
        output = output[:-6]
    else:
        dirty = False

    tag, distance, node = output.rsplit("-", 2)

    distance = int(distance)

    for i, c in enumerate(tag):
        if c.isdigit():
            semver_str = tag[i:]
            break
    else:
        semver_str = tag

    match = re.match(semver_pattern, semver_str)
    if match is None:
        semver = SemVer(0, 0, 0)
    else:
        semver = SemVer(
            int(match['major'] or '0'),
            int(match['minor'] or '0'),
            int(match['patch'] or '0'),
            match['prerelease'] or '',
            match['buildmetadata'] or '',
        )

    return tag, semver, distance, node, dirty
