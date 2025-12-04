#!/usr/bin/env python3
# coding: utf-8

import difflib
import json
import logging
import multiprocessing
import os
import pathlib
import pprint
import re
import sys
import subprocess
from typing import Any
import tempfile

from launchpadlib import errors as lp_errors  # fades
from launchpadlib.credentials import (RequestTokenAuthorizationEngine,
                                      UnencryptedFileCredentialStore)
from launchpadlib.launchpad import Launchpad
import requests  # fades


logger = logging.getLogger("mir.process_snaps")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

APPLICATION = "mir-ci"
LAUNCHPAD = "production"
DEFAULT_RELEASE = "noble"
TEAM = "mir-team"
SOURCE_NAME = "mir"

MESA_2404_PATHS = {
    "check-paths": {
        "snap/{architecture[0]}.list":
            "https://raw.githubusercontent.com/canonical/gpu-snap/refs/heads/main/lists/mesa-2404.{architecture[0]}.list"
    }
}

SNAPS = {
    "checkbox-mir": {
        "edge": {"ppa": "release", "recipe": "checkbox-mir-edge", "release": "jammy"},
    },
    "confined-shell": {
        "beta": {"ppa": "rc", "recipe": "confined-shell-beta"},
        "edge": {"ppa": "dev", "recipe": "confined-shell-edge"},
    },
    "graphics-test-tools": {
        "20/beta": {"recipe": "graphics-test-tools-20-beta"},
        "22/beta": {"recipe": "graphics-test-tools-22-beta"},
        "24/beta": {"recipe": "graphics-test-tools-24-beta"},
    },
    "mir-kiosk": {
        "beta": {"ppa": "rc", "recipe": "mir-kiosk-beta", "release": "focal"},
    },
    "mir-kiosk-kodi": {
        "edge": {"recipe": "mir-kiosk-kodi-edge", "non-uniform": True},
    },
    "mir-kiosk-neverputt": {
        "edge": {"recipe": "mir-kiosk-neverputt-edge"},
    },
    "mir-kiosk-scummvm": {
        "edge": {"recipe": "mir-kiosk-scummvm-edge"},
    },
    "mir-test-tools": {
        "20/beta": {"ppa": "rc", "recipe": "mir-test-tools-20-beta", "release": "focal"},
        "22/beta": {"ppa": "rc", "recipe": "mir-test-tools-22-beta", "release": "jammy"},
        "24/beta": {"ppa": "rc", "recipe": "mir-test-tools-24-beta"},
        "24/edge": {"ppa": "dev", "recipe": "mir-test-tools-24-edge"},
    },
    "miriway": {
        "beta": {"ppa": "rc", "recipe": "miriway-beta"},
        "edge": {"ppa": "dev", "recipe": "miriway-edge"},
    },
    "ubuntu-frame": {
        "20/beta": {"ppa": "rc", "recipe": "ubuntu-frame-20-beta", "release": "focal"},
        "22/beta": {"ppa": "rc", "recipe": "ubuntu-frame-22-beta", "release": "jammy"},
        "24/beta": {"ppa": "rc", "recipe": "ubuntu-frame-24-beta"},
        "24/edge": {"ppa": "dev", "recipe": "ubuntu-frame-24-edge"},
    },
    "ubuntu-frame-osk": {
        "20/beta": {"recipe": "ubuntu-frame-osk-20-beta"},
        "22/beta": {"recipe": "ubuntu-frame-osk-22-beta"},
        "24/beta": {"recipe": "ubuntu-frame-osk-24-beta"},
        "24/edge": {"recipe": "ubuntu-frame-osk-24-edge"},
    },
    "ubuntu-frame-vnc": {
        "20/beta": {"recipe": "ubuntu-frame-vnc-20-beta"},
        "22/beta": {"recipe": "ubuntu-frame-vnc-22-beta"},
        "24/beta": {"recipe": "ubuntu-frame-vnc-24-beta"},
        "24/edge": {"recipe": "ubuntu-frame-vnc-24-edge"},
    },
    "mesa-core20": {
        "beta": {"recipe": "mesa-core20-beta"},
    },
    "mesa-core22": {
        "beta": {"recipe": "mesa-core22-beta"},
    },
    "mesa-2404": {
        "stable": {"recipe": "mesa-2404-beta", "check-usns": False, **MESA_2404_PATHS},
        "beta": {"recipe": "mesa-2404-beta", **MESA_2404_PATHS},
        "asahi/beta": {"recipe": "mesa-2404-asahi-beta"},
    },
    "nvidia-core22": {
        "edge": {"recipe": "nvidia-core22-edge"},
    },
}

PENDING_BUILD = (
    "Needs building",
    "Dependency wait",
    "Currently building",
    "Uploading build",
)


FAILED_BUILD = (
    "Failed to build",
)


IGNORED_SOURCES = (
    "Deleted",
    "Obsolete",
)

# See https://regex101.com/r/b8otIx/2
MIR_VERSION_RE = re.compile(r"^(?P<version>[0-9\.]+)"              # major.minor.patch
                            r"(?:(?P<build>[+~](?:rc|dev)[0-9]+)"  # optional [~+]{rc,dev}* build tag
                            r"-g(?P<commit>[0-9a-f]+))?"           # ... with git suffix
                            r"-(?P<distro>[^-]+)$")                # distro

SNAP_VERSION_RE = re.compile(r"^(?:(?P<server>.+)-mir)?"
                             r"(?P<mir>.+?)"
                             r"(?:-snap(?P<snap>.+))?$")

STORE_URL = ("https://api.snapcraft.io/api/v1/snaps"
             "/details/{snap}?channel={channel}")
STORE_HEADERS = {
    "X-Ubuntu-Series": "16",
    "X-Ubuntu-Architecture": "{arch}"
}

CHECK_NOTICES_PATH = "/snap/bin/review-tools.check-notices"
CHECK_NOTICES_ARGS = []


def get_store_snap(processor, snap, channel):
    logger.debug("Checking for snap %s on %s in channel %s", snap, processor, channel)
    data = {
        "snap": snap,
        "channel": channel,
        "arch": processor,
    }
    resp = requests.get(
        STORE_URL.format(**data),
        headers={k: v.format(**data) for k, v in STORE_HEADERS.items()}
    )
    logger.debug("Got store response: %s", resp)

    try:
        result = json.loads(resp.content)
    except json.JSONDecodeError:
        logger.error("Could not parse store response: %s",
                     resp.content)
    else:
        return result


def fetch_url(entry: tuple[Any, pathlib.Path, str]):
    """
    Fetch a URL to a destination file if it does not exist.
    """
    context, dest, uri = entry
    if not dest.exists():
        r = requests.get(uri, stream=True)
        logger.debug("Downloading %s to %s…", uri, dest)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r:
                    f.write(chunk)
    return context, dest


def fetch_snaps(dir, store_snaps):
    """
    Download snaps from the store to a temporary directory.
    """
    return multiprocessing.Pool(8).map(
        fetch_url,
        ((snap,
          pathlib.Path(dir) / f"{snap['package_name']}_{snap['revision']}.snap",
          snap["download_url"])
            for snap in store_snaps)
    )


def check_snap_notices(dir, store_snaps):
    """
    Check the USN notices for the snaps.
    """
    snaps = fetch_snaps(dir, store_snaps)

    try:
        notices = subprocess.check_output([CHECK_NOTICES_PATH] + CHECK_NOTICES_ARGS + [s[1] for s in snaps])
        logger.debug("Got check_notices output:\n%s", notices.decode())
    except subprocess.CalledProcessError as e:
        logger.error("Failed to check notices:\n%s", e.output)
    else:
        notices = json.loads(notices)
        return notices


def check_paths(dir, store_snaps, paths):
    """
    Compare the contents of the snapped files with those at the URLs
    specified in the paths dictionary.
    """
    errors = []
    for snap, dest in fetch_snaps(dir, store_snaps):
        for k, v in paths.items():
            try:
                res = requests.get(v.format_map(snap))
                res.raise_for_status()
            except requests.exceptions.RequestException as ex:
                msg = f"Failed to download list:\n  {res.url}\n  {ex}"
                errors.append(RuntimeError(msg))
                logger.error(msg)

            try:
                squash_path = k.format_map(snap)
                snapped_contents = subprocess.check_output(("unsquashfs", "-cat", dest, squash_path))
            except subprocess.CalledProcessError as ex:
                msg = f"Failed to unsquash list:\n  {dest.name}\n  {ex}"
                errors.append(RuntimeError(msg))
                logger.error(msg)

            if res.content != snapped_contents:
                msg = f"Paths differ: {dest.name}:{squash_path} vs. {res.url}"
                errors.append(ValueError(msg))
                logger.error(f"::error::{msg}")
                logger.error(
                    "\n".join(difflib.unified_diff(res.content.decode("utf-8").splitlines(),
                                                   snapped_contents.decode("utf-8").splitlines()))
                )

    return errors


if __name__ == '__main__':
    try:
        lp = Launchpad.login_with(
            APPLICATION,
            LAUNCHPAD,
            version="devel",
            authorization_engine=RequestTokenAuthorizationEngine(LAUNCHPAD,
                                                                 APPLICATION),
            credential_store=UnencryptedFileCredentialStore(os.path.expanduser(sys.argv[1])),
        )
    except NotImplementedError:
        raise RuntimeError("Invalid credentials.")

    check_notices = (os.path.isfile(CHECK_NOTICES_PATH)
                     and os.access(CHECK_NOTICES_PATH, os.X_OK)
                     and CHECK_NOTICES_PATH)
    if not check_notices:
        logger.info("`review-tools` not found, skipping USN checks…")

    ubuntu = lp.distributions["ubuntu"]
    logger.debug("Got ubuntu: %s", ubuntu)

    serie = {}

    def getSeries(name):
        if name in serie:
             return serie[name]

        serie[name] = ubuntu.getSeries(name_or_version=name)
        logger.debug("Got series: %s", serie[name])
        return serie[name]

    team = lp.people[TEAM]
    logger.debug("Got team: %s", team)

    errors = []

    for snap, channels in SNAPS.items():
        for channel, snap_map in channels.items():
            logger.info("Processing channel %s for snap %s…", channel, snap)

            archive = ubuntu.main_archive

            try:
                snap_recipe = lp.snaps.getByName(owner=team, name=snap_map["recipe"])
                logger.debug("Got snap: %s", snap_recipe)
            except lp_errors.NotFound as ex:
                logger.error("::error::Snap recipe not found: %s", snap_map["recipe"])
                errors.append(ex)
                continue

            if "ppa" in snap_map:
                archive = team.getPPAByName(name=snap_map["ppa"])
                latest_source = None
                logger.debug("Got ppa: %s", archive)

                sources = archive.getPublishedSources(
                    source_name=SOURCE_NAME,
                    distro_series=getSeries(snap_map.get("release", DEFAULT_RELEASE)))

                if not sources:
                    logger.error("::error::Did not find %s in %s/%s", SOURCE_NAME, TEAM, snap_map["ppa"])
                    continue

                for source in sources:
                    if source.status in IGNORED_SOURCES:
                        logger.debug("Ignoring source: %s (status: %s)", source.display_name, source.status)
                        continue
                    latest_source = source
                    break

                if not latest_source:
                    logger.error("::error::Did not find a valid source for %s in %s/%s", SOURCE_NAME, TEAM, snap_map["ppa"])
                    continue

                logger.debug("Latest source: %s", latest_source.display_name)

                mir_version = (
                    "".join(v or "" for v in MIR_VERSION_RE.fullmatch(latest_source.source_package_version).groups()[0:2])
                )
                logger.debug("Parsed upstream version: %s", mir_version)

                if latest_source.status != "Published":
                    logger.info("Skipping %s: %s",
                                latest_source.display_name, latest_source.status)
                    continue

                builds = latest_source.getBuilds()

                if failed_builds := tuple(build for build in builds if build.buildstate in FAILED_BUILD):
                    for build in failed_builds:
                        logger.error("::error::Build failed: %s", build.web_link)
                    errors.append(RuntimeError("One or more builds failed"))
                    continue

                if any(build.buildstate in PENDING_BUILD for build in builds):
                    logger.info("Skipping %s: builds pending…",
                                latest_source.display_name)
                    continue

                if any(binary.status != "Published"
                    for binary in latest_source.getPublishedBinaries()):
                    logger.info("Skipping %s: binaries pending…",
                                latest_source.display_name)
                    continue
            else:
                mir_version = None

            if len(snap_recipe.pending_builds) > 0:
                logger.info("Skipping %s: snap builds pending…",
                            snap_recipe.web_link)
                continue

            store_snaps = tuple(filter(lambda snap: snap.get("result") != "error", (
                get_store_snap(processor.name,
                               snap,
                               channel)
                for processor in snap_recipe.processors
            )))

            versions = {snap["version"] for snap in store_snaps}
            versions_dict = {snap["architecture"][0]: snap["version"] for snap in store_snaps}
            if len(versions) > 1 and not snap_map.get("non-uniform", False):
                logger.error("::error::Non-uniform versions of snap %s: %s", snap_recipe.web_link, versions_dict)
                errors.append(RuntimeError("Non-uniform versions of snap"))
            else:
                logger.debug("Got store versions: %s", versions_dict)

            with tempfile.TemporaryDirectory(dir=pathlib.Path.home()) as dir:
                if paths := snap_map.get("check-paths", {}):
                    errors.extend(check_paths(dir, store_snaps, paths))

                if all(store_snap is None
                   or mir_version is None
                   or mir_version == SNAP_VERSION_RE.match(store_snap["version"]).group("mir")
                   for store_snap in store_snaps):

                    if snap_map.get("check-usns", True) and check_notices:
                        snap_notices = check_snap_notices(dir, store_snaps)[snap]

                        if any(snap_notices.values()):
                            logger.info("Found USNs:\n%s", pprint.pformat(snap_notices))
                        else:
                            logger.info(
                                "Skipping %s: store versions are current and no USNs found",
                                snap
                            )
                            continue
                    else:
                        logger.info(
                            "Skipping %s: store versions are current and USN checks are disabled",
                            snap
                        )
                        continue

            # warning so it gets surfaced by GitHub Actions
            logger.info("::warning::Triggering %s…", snap_recipe.description or snap_recipe.name)

            snap_recipe.requestBuilds(archive=archive,
                                      pocket=snap_recipe.auto_build_pocket,
                                      channels=snap_map.get("channels", {}))
            logger.debug("Triggered builds: %s", snap_recipe.web_link)

    for error in errors:
        logger.debug(error)

    if errors:
        sys.exit(1)
