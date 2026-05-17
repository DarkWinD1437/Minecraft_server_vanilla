from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path


class ContainerState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    NOT_CREATED = "not_created"
    UNKNOWN = "unknown"


class DockerClient:
    def __init__(self, compose_dir: Path | None = None) -> None:
        self.compose_dir = compose_dir or Path(__file__).parent.parent.parent
        self.compose_cmd = self._detect_compose_cmd()

    def _detect_compose_cmd(self) -> list[str]:
        """Auto-detect 'docker compose' (v2) or 'docker-compose' (v1)."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return ["docker", "compose"]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return ["docker-compose"]

    def _run(self, cmd: list[str], timeout: int = 15) -> tuple[str, str]:
        """Run a command and return (stdout, stderr). Never raises."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                timeout=timeout, cwd=str(self.compose_dir)
            )
            return result.stdout.strip(), result.stderr.strip()
        except FileNotFoundError:
            return "", "Docker no encontrado. ¿Está instalado y en el PATH?"
        except subprocess.TimeoutExpired:
            return "", f"Timeout al ejecutar: {' '.join(cmd)}"
        except Exception as e:
            return "", str(e)

    def get_container_state(self, name: str) -> ContainerState:
        out, err = self._run(
            ["docker", "ps", "-a", "--filter", f"name=^{name}$",
             "--format", "{{.State}}"]
        )
        if err and not out:
            return ContainerState.UNKNOWN
        if not out:
            return ContainerState.NOT_CREATED
        state = out.strip().lower()
        if state == "running":
            return ContainerState.RUNNING
        if state in ("exited", "created", "dead", "removing"):
            return ContainerState.STOPPED
        if state == "paused":
            return ContainerState.PAUSED
        return ContainerState.UNKNOWN

    def start(self, service: str | None = None) -> tuple[str, str]:
        cmd = self.compose_cmd + ["up", "-d"]
        if service:
            cmd.append(service)
        return self._run(cmd, timeout=120)

    def stop(self, service: str | None = None) -> tuple[str, str]:
        if service:
            out, err = self._run(["docker", "stop", service], timeout=30)
        else:
            out, err = self._run(self.compose_cmd + ["down"], timeout=60)
        return out, err

    def restart(self, container: str) -> tuple[str, str]:
        return self._run(["docker", "restart", container], timeout=60)

    def get_logs(self, container: str, tail: int = 100) -> tuple[str, str]:
        return self._run(
            ["docker", "logs", "--tail", str(tail), container], timeout=15
        )

    def get_stats(self, container: str) -> tuple[dict, str]:
        out, err = self._run(
            ["docker", "stats", "--no-stream", "--format", "{{json .}}", container],
            timeout=10
        )
        if not out:
            return {}, err
        try:
            # docker stats may output multiple JSON lines; take last non-empty
            lines = [l for l in out.splitlines() if l.strip()]
            return json.loads(lines[-1]), ""
        except (json.JSONDecodeError, IndexError) as e:
            return {}, str(e)

    def exec_command(self, container: str, command: str) -> tuple[str, str, int]:
        """Run a command inside a container. Returns (stdout, stderr, returncode)."""
        try:
            result = subprocess.run(
                ["docker", "exec", container] + command.split(),
                capture_output=True, text=True, encoding="utf-8", timeout=10,
                cwd=str(self.compose_dir)
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except Exception as e:
            return "", str(e), -1

    def get_container_info(self, container: str) -> tuple[dict, str]:
        out, err = self._run(["docker", "inspect", "--format", "{{json .}}", container])
        if not out:
            return {}, err
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                return data[0], ""
            return data, ""
        except json.JSONDecodeError as e:
            return {}, str(e)

    def get_compose_services(self) -> list[str]:
        out, _ = self._run(self.compose_cmd + ["ps", "--services"])
        return [s for s in out.splitlines() if s.strip()]

    def pull_images(self) -> tuple[str, str]:
        return self._run(self.compose_cmd + ["pull"], timeout=300)

    def is_docker_running(self) -> bool:
        out, err = self._run(["docker", "info"], timeout=5)
        return bool(out) and not err
