import json
import threading
import time
from queue import Queue, Empty
import websocket



import game.multiplayer.multiplayer_config as mconfig


class WSClient:
    """
    Minimaler WebSocket-Client für Games:
    - verbindet im Hintergrund
    - send_json() ist non-blocking (queued)
    - poll() liefert eingehende Messages (non-blocking)
    - status: connected/disconnected
    """

    def __init__(self, reconnect: bool = True, reconnect_delay_s: float = 1.0):
        self.url = f"{mconfig.MULTIPLAYER_WS_URL}{mconfig.CODE}?token={mconfig.PLAYER_TOKEN}"
        print(f"Connecting to {self.url}")

        self.reconnect = reconnect
        self.reconnect_delay_s = reconnect_delay_s

        self._incoming: Queue[dict] = Queue()
        self._outgoing: Queue[str] = Queue()
        self._status: Queue[bool] = Queue(maxsize=1)

        self._ws = None
        self._thread = None
        self._stop = False
        self._connected = False
        self._started = False

    def start(self):
        """Startet den Background-Thread genau einmal."""
        if self._started:
            return
        self._started = True
        mconfig.check_connection(status=False)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Beendet den Client (Thread endet, Verbindung wird geschlossen)."""
        self._stop = True
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass

        mconfig.check_connection(status=True)

    def is_connected(self) -> bool:
        return self._connected

    def poll_status(self) -> bool | None:
        """Non-blocking: True/False wenn neuer Status da, sonst None."""
        try:
            return self._status.get_nowait()
        except Empty:
            return None

    def poll(self) -> dict | None:
        """Non-blocking: nächste eingehende JSON-Message oder None."""
        try:
            return self._incoming.get_nowait()
        except Empty:
            return None

    def send_json(self, msg: dict):
        """Non-blocking: queued JSON -> wird im WS-Thread gesendet."""
        self._outgoing.put(json.dumps(msg))

    # ---------------- internal ----------------

    def _build_url(self):
        code = mconfig.CODE
        token = mconfig.PLAYER_TOKEN
        if not code or not token:
            return None
        return f"{mconfig.MULTIPLAYER_WS_URL}{code}?token={token}"

    def _set_connected(self, value: bool):
        self._connected = value
        # Queue maxsize=1: immer nur neuesten Status behalten
        try:
            while True:
                self._status.get_nowait()
        except Empty:
            pass
        self._status.put(value)

    def _drain_outgoing(self):
        """Sendet alle queued Messages (läuft im WS-Thread)."""

        if not self._ws:
            return
        while True:
            try:
                raw = self._outgoing.get_nowait()
            except Empty as error:
                break
            try:
                self._ws.send(raw)
            except Exception as error:
                print(f"Fehler beim Senden: {error}")
                break

    def _run(self):
        while not self._stop:
            try:

                self._ws = websocket.create_connection(self.url, timeout=2.0)
                self._ws.settimeout(0.2)  # kurzer recv timeout, damit wir outgoing oft flushen
                self._set_connected(True)

                while not self._stop:
                    # 1) outgoing flushen
                    self._drain_outgoing()

                    # 2) incoming lesen (non-blocking mit timeout)
                    try:
                        raw = self._ws.recv()
                        if raw is None:
                            raise RuntimeError("WS closed")
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            msg = {"type": "raw", "data": raw}
                        self._incoming.put(msg)
                    except websocket.WebSocketTimeoutException:
                        # normal, weil settimeout kurz ist
                        pass

            except Exception:
                self._set_connected(False)
                try:
                    if self._ws:
                        self._ws.close()
                except Exception:
                    pass
                self._ws = None

                if not self.reconnect or self._stop:
                    break
                time.sleep(self.reconnect_delay_s)

        self._set_connected(False)