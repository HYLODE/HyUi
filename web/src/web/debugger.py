# debugger.py
# https://blog.theodo.com/2020/05/debug-flask-vscode/
from os import getenv


def initialize_flask_server_debugger_if_needed() -> None:
    if getenv("DEBUGGER") == "True":
        import multiprocessing

        if multiprocessing.current_process().pid > 1:  # type: ignore
            import debugpy

            debugpy.listen(("0.0.0.0", 10001))
            print(
                "⏳ VS Code debugger can now be attached, press F5 in VS Code ⏳",
                flush=True,
            )
            debugpy.wait_for_client()
            print("🎉 VS Code debugger attached, enjoy debugging 🎉", flush=True)
