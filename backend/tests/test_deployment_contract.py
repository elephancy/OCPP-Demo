import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def application_workflows() -> str:
    return "\n".join(path.read_text() for path in sorted(
        (REPOSITORY_ROOT / ".github/workflows").glob("*.y*ml")))


def test_production_release_authority_is_absent_from_application_workflows() -> None:
    assert not (REPOSITORY_ROOT / ".github/workflows/deploy-production.yml").exists()
    assert not (REPOSITORY_ROOT / ".github/hetzner-release.json").exists()
    workflow = application_workflows()
    assert "HetznerReleaseGateway/" not in workflow
    assert "id-token: write" not in workflow
    assert "secrets: inherit" not in workflow


def test_caller_and_docs_expose_no_direct_host_deployment_surface() -> None:
    workflow = application_workflows()
    readme = (REPOSITORY_ROOT / "README.md").read_text()

    assert not re.search(r"\$\{\{\s*secrets\.", workflow, re.IGNORECASE)
    assert not re.search(
        r"\b(?:ssh|scp|rsync)\b|/opt/|HETZNER_(?:HOST|USER|PATH|SSH_KEY)",
        workflow,
        re.IGNORECASE,
    )
    assert not re.search(
        r"\b(?:ssh|scp|rsync)\b|/opt/|"
        r"HETZNER_(?:HOST|USER|PATH|SSH_KEY)|git\s+pull|/mnt/[a-z]/",
        readme,
        re.IGNORECASE,
    )
    assert not (REPOSITORY_ROOT / "deploy/Caddyfile.host.example").exists()


def test_application_build_inputs_remain_available() -> None:
    for component in ("backend", "frontend", "simulator"):
        dockerfile = REPOSITORY_ROOT / component / "Dockerfile"
        assert dockerfile.is_file()
        assert re.search(r"^FROM\s+", dockerfile.read_text(), re.MULTILINE)
