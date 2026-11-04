"""Optional container regression for the trusted-artifact/user ownership boundary."""

import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import uuid

import yaml

TASK = yaml.safe_load(
    (
        Path(__file__).resolve().parents[1]
        / "task/prepare-plugin-oci-ta/prepare-plugin-oci-ta.yaml"
    ).read_text()
)["spec"]


@unittest.skipUnless(
    os.environ.get("PLUGIN_PREPARE_TEST_IMAGE"),
    "Set PLUGIN_PREPARE_TEST_IMAGE for Podman regression",
)
class PreparationOwnership(unittest.TestCase):
    def test_root_owned_archive_can_be_restored_and_packaged_without_root(self):
        image = os.environ["PLUGIN_PREPARE_TEST_IMAGE"]
        volume = "plugin-preparation-regression-" + uuid.uuid4().hex

        def run(uid, command, *, content=None, check=True):
            return subprocess.run(
                [
                    "podman",
                    "run",
                    "--rm",
                    "--platform",
                    "linux/amd64",
                    "--user",
                    str(uid),
                    "--interactive",
                    "--volume",
                    volume + ":/var/workdir",
                    "--entrypoint",
                    command[0],
                    image,
                    *command[1:],
                ],
                input=content,
                capture_output=True,
                check=check,
                timeout=120,
            )

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            skill = source / "pack/skills/demo"
            skill.mkdir(parents=True)
            (source / "pack/AGENTS.md").write_text("Use the demo.\n")
            (source / "pack/catalog-info.yaml").write_text(
                "kind: Location\nmetadata: {name: pack}\n"
            )
            (source / "pack/pack-plugin.yaml").write_text(
                yaml.safe_dump(
                    {
                        "kind": "AiResource",
                        "metadata": {
                            "name": "pack",
                            "annotations": {
                                "agentic-plugins.redhat.com/version": "1.0",
                                "agentic.redhat.com/source": "redhat",
                            },
                        },
                        "spec": {"type": "plugin", "lifecycle": "beta"},
                    }
                )
            )
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: A demo\n---\nUse the demo.\n"
            )
            (skill / "catalog-info.yaml").write_text(
                "kind: AiResource\nmetadata: {name: demo}\nspec: {type: skill}\n"
            )
            stream = io.BytesIO()

            def root_owned(member):
                member.uid = member.gid = 0
                member.uname = member.gname = "root"
                member.mode = 0o755 if member.isdir() else 0o644
                return member

            with tarfile.open(fileobj=stream, mode="w:gz") as archive:
                archive.add(source, arcname=".", filter=root_owned)
            subprocess.run(
                ["podman", "volume", "create", volume], check=True, capture_output=True
            )
            try:
                # Model the fsGroup-writable emptyDir and the original root restore.
                run(
                    0,
                    [
                        "bash",
                        "-c",
                        "chmod 0777 /var/workdir; mkdir /var/workdir/source; tar -xzpf - -C /var/workdir/source",
                    ],
                    content=stream.getvalue(),
                )
                package = [
                    "python",
                    "-m",
                    "src.component",
                    "package",
                    "--source",
                    "/var/workdir/source",
                    "--plugin",
                    "pack",
                    "--revision",
                    "a" * 40,
                    "--source-url",
                    "https://example.com/source",
                    "--output",
                    "/var/workdir/source/.konflux/package",
                ]
                failed = run(1001, package, check=False)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn(b"Permission denied", failed.stderr)
                run(0, ["bash", "-c", "rm -rf /var/workdir/source"])
                uid = TASK["stepTemplate"]["securityContext"]["runAsUser"]
                run(
                    uid,
                    [
                        "bash",
                        "-c",
                        "mkdir /var/workdir/source; tar -xzpf - -C /var/workdir/source",
                    ],
                    content=stream.getvalue(),
                )
                result = run(uid, package)
                self.assertEqual(json.loads(result.stdout)["skills"], 1)
                packed = run(
                    uid, ["tar", "-czf", "-", "-C", "/var/workdir/source", "."]
                )
                with tarfile.open(
                    fileobj=io.BytesIO(packed.stdout), mode="r:gz"
                ) as archive:
                    manifest = json.load(
                        archive.extractfile("./.konflux/package/manifest.json")
                    )
                self.assertEqual(manifest["skills"], ["pack/demo"])
            finally:
                subprocess.run(
                    ["podman", "volume", "rm", "--force", volume],
                    check=True,
                    capture_output=True,
                )
