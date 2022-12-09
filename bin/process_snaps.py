#!/usr/bin/env python3
# coding: utf-8

import json
import logging
import multiprocessing
import os
import pathlib
import pprint
import re
import sys
import subprocess
import tempfile

from launchpadlib import errors as lp_errors  # fades
from launchpadlib.credentials import (RequestTokenAuthorizationEngine,
                                      UnencryptedFileCredentialStore)
from launchpadlib.launchpad import Launchpad
import requests  # fades


logger = logging.getLogger("mir.process_snaps")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

APPLICATION = "mir-ci"
LAUNCHPAD = "production"
DEFAULT_RELEASE = "focal"
TEAM = "mir-team"
SOURCE_NAME = "mir"

SNAPS = {
    "mir-kiosk": {
        "edge": {"ppa": "dev", "recipe": "mir-kiosk-edge"},
        "beta": {"ppa": "rc", "recipe": "mir-kiosk-beta"},
    },
    "mir-test-tools": {
        "edge": {"ppa": "dev", "recipe": "mir-test-tools-20-edge"},
        "beta": {"ppa": "rc", "recipe": "mir-test-tools-20-beta"},
    },
    "egmde": {
        "edge": {"ppa": "dev", "recipe": "egmde-mir-edge"},
        "beta": {"ppa": "rc", "recipe": "egmde-mir-beta"},
    },
    "egmde-confined-desktop": {
        "edge": {"ppa": "dev", "recipe": "egmde-confined-desktop-edge"},
        "beta": {"ppa": "rc", "recipe": "egmde-confined-desktop-beta"},
    },
    "ubuntu-frame": {
        "edge": {"ppa": "dev", "recipe": "ubuntu-frame-20-edge"},
        "beta": {"ppa": "rc", "recipe": "ubuntu-frame-20-beta"},
        "22/edge": {"ppa": "dev", "recipe": "ubuntu-frame-22-edge", "release": "jammy"},
    },
    "ubuntu-frame-osk": {
        "beta": {"recipe": "ubuntu-frame-osk-20-beta"},
    },
    "ubuntu-frame-vnc": {
        "beta": {"recipe": "ubuntu-frame-vnc-20-beta"},
        "edge": {"recipe": "ubuntu-frame-vnc-20-edge"},
    },
    "mesa-core20": {
        "beta": {"recipe": "mesa-core20-beta"},
    },
    "mir-kiosk-x11": {
        "edge": {"ppa": "dev", "recipe": "mir-kiosk-x11-edge"},
        "beta": {"ppa": "rc", "recipe": "mir-kiosk-x11-beta"},
    },
}

PENDING_BUILD = (
    "Needs building",
    "Dependency wait",
    "Currently building",
    "Uploading build",
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


def fetch_url(entry):
    dest, uri = entry
    r = requests.get(uri, stream=True)
    logger.debug("Downloading %s to %s…", uri, dest)
    if r.status_code == 200:
        with open(dest, "wb") as f:
            for chunk in r:
                f.write(chunk)
    return dest


def check_snap_notices(store_snaps):
    with tempfile.TemporaryDirectory(dir=pathlib.Path.home()) as dir:
        snaps = multiprocessing.Pool(8).map(
            fetch_url,
            ((pathlib.Path(dir) / f"{snap['package_name']}_{snap['revision']}.snap",
                snap["download_url"])
                for snap in store_snaps)
        )

        try:
            notices = subprocess.check_output([CHECK_NOTICES_PATH] + snaps)
            logger.debug("Got check_notices output:\n%s", notices.decode())
        except subprocess.CalledProcessError as e:
            logger.error("Failed to check notices:\n%s", e.output)
        else:
            notices = json.loads(notices)
            return notices


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

            try:
                snap_recipe = lp.snaps.getByName(owner=team, name=snap_map["recipe"])
                logger.debug("Got snap: %s", snap_recipe)
            except lp_errors.NotFound as ex:
                logger.error("Snap recipe not found: %s", snap_map["recipe"])
                errors.append(ex)
                continue

            if "ppa" in snap_map:
                ppa = team.getPPAByName(name=snap_map["ppa"])
                latest_source = None
                logger.debug("Got ppa: %s", ppa)

                sources = ppa.getPublishedSources(
                    source_name=SOURCE_NAME,
                    distro_series=getSeries(snap_map.get("release", DEFAULT_RELEASE)))

                if not sources:
                    logger.error("Did not find %s in %s/%s", SOURCE_NAME, TEAM, snap_map["ppa"])
                    continue

                for source in sources:
                    if source.status in IGNORED_SOURCES:
                        logger.debug("Ignoring source: %s (status: %s)", source.display_name, source.status)
                        continue
                    latest_source = source
                    break

                if not latest_source:
                    logger.error("Did not find a valid source for %s in %s/%s", SOURCE_NAME, TEAM, snap_map["ppa"])
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

                if any(build.buildstate in PENDING_BUILD
                    for build in latest_source.getBuilds()):
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

            logger.debug("Got store versions: %s", {snap["architecture"][0]: snap["version"] for snap in store_snaps})

            if all(store_snap is None
                   or mir_version is None
                   or mir_version == SNAP_VERSION_RE.match(store_snap["version"]).group("mir")
                   for store_snap in store_snaps):

                if check_notices:
                    snap_notices = check_snap_notices(store_snaps)[snap]

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
                        "Skipping %s: store versions are current",
                        snap
                    )
                    continue

            logger.info("Triggering %s…", snap_recipe.description or snap_recipe.name)

            snap_recipe.requestBuilds(archive=ppa,
                                      pocket=snap_recipe.auto_build_pocket)
            logger.debug("Triggered builds: %s", snap_recipe.web_link)

    for error in errors:
        logger.debug(error)

    if errors:
        sys.exit(1)
