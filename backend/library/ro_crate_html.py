import json
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

RO_CRATE_HTML_PREVIEW_NAME = "ro-crate-preview.html"
ROCHTML_BINARY = "rochtml"


def generate_html_preview(ro_crate_json):
    """Render an offline HTML preview of an RO-Crate JSON-LD graph via the
    `rochtml` CLI (ro-crate-html-js). Returns the HTML bytes, or None if
    generation failed - callers should treat this as best-effort."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        metadata_path = os.path.join(tmp_dir, "ro-crate-metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as handle:
            json.dump(ro_crate_json, handle, ensure_ascii=False)

        try:
            subprocess.run(
                [ROCHTML_BINARY, metadata_path],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
            logger.warning(
                "RO-Crate HTML preview generation failed: %s\n%s", exc, stderr
            )
            return None
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("RO-Crate HTML preview generation failed: %s", exc)
            return None

        preview_path = os.path.join(tmp_dir, RO_CRATE_HTML_PREVIEW_NAME)
        try:
            with open(preview_path, "rb") as handle:
                return handle.read()
        except OSError as exc:
            logger.warning("RO-Crate HTML preview file missing: %s", exc)
            return None
