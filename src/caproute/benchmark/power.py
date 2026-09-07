from __future__ import annotations

import subprocess
import threading


class PowerSampler:
    def __init__(self, interval_seconds: float = 0.5) -> None:
        self.interval_seconds = interval_seconds
        self.samples: list[float] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5, check=True,
                )
                self.samples.append(float(result.stdout.strip().splitlines()[0]))
            except (OSError, subprocess.SubprocessError, ValueError, IndexError):
                pass
            self._stop.wait(self.interval_seconds)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, elapsed: float) -> dict:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=max(1.0, 2 * self.interval_seconds))
        average = sum(self.samples) / len(self.samples) if self.samples else None
        return {
            "power_samples": len(self.samples),
            "power_watts_mean": average,
            "energy_joules_gross": average * elapsed if average is not None else None,
        }

