# main.py
"""
Application entrypoint.
Integrates Qt and asyncio with qasync.run and connects a clean shutdown handler.
"""
import sys
import asyncio
from qasync import QApplication as QAsyncApplication, run
from PySide6.QtCore import QCoreApplication

from app_controller import AppController

# A cancelable Future used to keep the asyncio loop alive until the Qt app quits.
_future_keep_alive = None

async def _wait_for_app_exit():
    """Hold the running asyncio loop until the Future is cancelled on shutdown."""
    global _future_keep_alive
    _future_keep_alive = asyncio.get_running_loop().create_future()
    try:
        await _future_keep_alive
    except asyncio.CancelledError:
        # expected on shutdown
        pass

def _shutdown_async_loop():
    """Synchronous callback: cancel the keep-alive future so asyncio tasks can exit."""
    global _future_keep_alive
    if _future_keep_alive and not _future_keep_alive.done():
        print("Cancelling async loop keep-alive for graceful shutdown...")
        _future_keep_alive.cancel()

def main():
    qapp = QAsyncApplication(sys.argv)

    # Hook to cancel the asyncio keep-alive when Qt is exiting
    QCoreApplication.instance().aboutToQuit.connect(_shutdown_async_loop)

    # Instantiate controller (which constructs model + view)
    controller = AppController()
    controller.show()

    print("Starting qasync (merged Qt + asyncio) event loops...")
    try:
        # Run until the keep-alive finishes (cancelled on Qt exit)
        run(_wait_for_app_exit())
    except Exception as e:
        print("Unhandled exception in application:", e)
    finally:
        print("Application exiting.")

if __name__ == "__main__":
    main()
