from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock
import json
import os
import plistlib
import subprocess
import sys
import watertime as w

def inspect_shortcut():
    env = dict(os.environ, PIVORA_TEST_LINK=str(w.windows_startup_shortcut()))
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
        "$l = (New-Object -ComObject WScript.Shell).CreateShortcut($env:PIVORA_TEST_LINK); "
        "@{Target=$l.TargetPath; Arguments=$l.Arguments; Directory=$l.WorkingDirectory} | ConvertTo-Json -Compress"],
        env=env, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)

with TemporaryDirectory(prefix="Pivora's startup ") as tmp:
    folder = Path(tmp)
    for platform in (sys.platform,):
        for frozen in (False, True):
            executable = {
                "win32": folder / "Pivora.exe",
                "linux": folder / "Pivora %f",
                "darwin": folder / "Pivora.app/Contents/MacOS/Pivora",
            }[platform] if frozen else Path(sys.executable)
            executable.parent.mkdir(parents=True, exist_ok=True)
            if frozen:
                executable.touch()
            script = str(Path(w.__file__).resolve())
            with patch.dict(os.environ, APPDATA=tmp, XDG_CONFIG_HOME=tmp), patch.object(Path, "home", return_value=folder), patch.object(w, "IS_MACOS", platform == "darwin"), patch.object(sys, "platform", platform), patch.object(sys, "frozen", frozen, create=True), patch.object(sys, "executable", str(executable)):
                assert not w.is_autostart_enabled()
                w.set_autostart(True)
                assert w.is_autostart_enabled()
                w.set_autostart(True)
                if platform == "win32":
                    link = inspect_shortcut()
                    target = executable if frozen else executable.with_name("pythonw.exe")
                    if not target.exists():
                        target = executable
                    assert Path(link["Target"]) == target, link
                    assert link["Arguments"] == subprocess.list2cmdline(([] if frozen else [script]) + ["--minimized"]), link
                    assert os.path.samefile(link["Directory"], target.parent), link
                elif platform == "linux":
                    content = w.linux_autostart_path().read_text(encoding="utf-8")
                    assert "Exec=" + w.desktop_exec([str(executable), *([] if frozen else [script]), "--minimized"]) in content
                    assert ("%%f" in content) == frozen
                    subprocess.run(["desktop-file-validate", str(w.linux_autostart_path())], check=True)
                else:
                    agent = plistlib.loads(w.macos_launch_agent_path().read_bytes())
                    expected = ["/usr/bin/open", "-a", str(executable.parents[2]), "--args"] if frozen else [str(executable), script]
                    assert agent["ProgramArguments"] == expected + ["--minimized"]
                    assert agent["RunAtLoad"] and agent["LimitLoadToSessionType"] == "Aqua"
                    subprocess.run(["plutil", "-lint", str(w.macos_launch_agent_path())], check=True)
                w.set_autostart(False)
                w.set_autostart(False)
                assert not w.is_autostart_enabled()
            print("PASS", platform, "packaged" if frozen else "source", "enable, re-enable, disable")

for tray in (None, Mock()):
    app = w.WatertimeApp.__new__(w.WatertimeApp)
    app.tray = tray
    app.root = Mock()
    app.hide_dashboard = Mock()
    app._show_dashboard_internal = Mock()
    with patch.object(sys, "argv", ["Pivora", "--minimized"]):
        app.run()
    if tray is None:
        app._show_dashboard_internal.assert_called_once()
    else:
        app.hide_dashboard.assert_called_once()
    app.root.mainloop.assert_called_once()
print("PASS minimized startup and dashboard fallback")

