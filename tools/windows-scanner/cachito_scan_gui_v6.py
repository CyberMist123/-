import asyncio
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from bleak import BleakScanner


OUTPUT = Path(__file__).resolve().parent / f"cachito-scan-{datetime.now():%Y%m%d-%H%M%S}.txt"
write_lock = threading.Lock()
last_seen: Dict[str, str] = {}

# (动作说明, 采样秒数)
# 连续滑块必须先调到目标值，再由用户确认开始采样。
TEST_STEPS: List[Tuple[str, int]] = [
    ("基线：吮吸 0；炮机 0；嗨翻关闭", 6),

    ("吮吸调到 1；炮机保持 0；嗨翻关闭", 6),
    ("吮吸调到 10；炮机保持 0；嗨翻关闭", 6),
    ("吮吸调到 25；炮机保持 0；嗨翻关闭", 6),
    ("吮吸调到 50；炮机保持 0；嗨翻关闭", 6),
    ("吮吸调到 75；炮机保持 0；嗨翻关闭", 6),
    ("吮吸调到 100；炮机保持 0；嗨翻关闭", 6),
    ("吮吸回到 0；炮机保持 0；嗨翻关闭", 6),

    ("炮机调到 1；吮吸保持 0；嗨翻关闭", 6),
    ("炮机调到 10；吮吸保持 0；嗨翻关闭", 6),
    ("炮机调到 25；吮吸保持 0；嗨翻关闭", 6),
    ("炮机调到 50；吮吸保持 0；嗨翻关闭", 6),
    ("炮机调到 75；吮吸保持 0；嗨翻关闭", 6),
    ("炮机调到 100；吮吸保持 0；嗨翻关闭", 6),
    ("炮机回到 0；吮吸保持 0；嗨翻关闭", 6),

    ("打开嗨翻/重力感应；手机平放、屏幕朝上", 6),
    ("保持嗨翻开启；手机竖直、屏幕朝向自己", 6),
    ("保持嗨翻开启；手机向左倾斜约 45°", 6),
    ("保持嗨翻开启；手机向右倾斜约 45°", 6),
    ("手机先平放；开始采样后，用约 12 秒完成：平放 → 竖直 → 平放", 12),
    ("关闭嗨翻；吮吸和炮机都回到 0", 6),
]


def hex_bytes(data: bytes) -> str:
    return data.hex().upper()


def append_log(text: str = "") -> None:
    with write_lock:
        with OUTPUT.open("a", encoding="utf-8") as f:
            f.write(text + "\n")


def beep(frequency: int = 1000, duration: int = 250) -> None:
    try:
        import winsound
        winsound.Beep(frequency, duration)
    except Exception:
        pass


def speak(text: str) -> None:
    if os.name != "nt":
        return

    def _worker() -> None:
        safe = text.replace("'", "''")
        command = (
            "$v=New-Object -ComObject SAPI.SpVoice;"
            "$v.Rate=1;"
            f"$null=$v.Speak('{safe}')"
        )
        try:
            subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
            )
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def on_advertisement(device, adv) -> None:
    address = getattr(device, "address", "unknown")
    name = adv.local_name or getattr(device, "name", None) or "-"
    rssi = getattr(adv, "rssi", None)

    manufacturer = {
        f"0x{company_id:04X}": hex_bytes(data)
        for company_id, data in sorted(adv.manufacturer_data.items())
    }
    service_data = {
        str(uuid): hex_bytes(data)
        for uuid, data in sorted(adv.service_data.items())
    }
    services = sorted(str(x) for x in adv.service_uuids)

    fingerprint = repr((name, services, manufacturer, service_data))
    if last_seen.get(address) == fingerprint:
        return
    last_seen[address] = fingerprint

    # 远距离且没有可分析字段的广播不记录。
    if (
        rssi is not None
        and rssi < -88
        and not manufacturer
        and not service_data
        and not services
    ):
        return

    append_log("")
    append_log(f"[BLE {datetime.now():%Y-%m-%d %H:%M:%S.%f}]")
    append_log(f"Address: {address}")
    append_log(f"RSSI: {rssi}")
    append_log(f"Name: {name}")
    append_log(f"Service UUIDs: {services}")
    append_log(f"Manufacturer Data: {manufacturer}")
    append_log(f"Service Data: {service_data}")


class ScannerThread:
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.thread = None
        self.loop = None
        self.stop_event = None
        self.started = threading.Event()

    def start(self) -> None:
        self.thread = threading.Thread(target=self._thread_main, daemon=True)
        self.thread.start()

    def _thread_main(self) -> None:
        try:
            asyncio.run(self._scan_main())
        except Exception as exc:
            self.status_callback(f"扫描失败：{exc}", True)

    async def _scan_main(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()

        scanner = BleakScanner(
            detection_callback=on_advertisement,
            scanning_mode="active",
        )

        await scanner.start()
        append_log("===== BLE SCAN STARTED =====")
        self.started.set()
        self.status_callback("BLE 扫描已启动", False)

        await self.stop_event.wait()

        await scanner.stop()
        append_log("===== BLE SCAN STOPPED =====")
        self.status_callback("BLE 扫描已停止", False)

    def stop(self) -> None:
        if self.loop and self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Cachito BLE 引导测试器 v6")
        self.root.geometry("920x620")
        self.root.minsize(820, 560)

        self.current_step = -1
        self.remaining = 0
        self.timer_job = None
        self.running = False
        self.paused = False
        self.phase = "idle"
        self.scanner_ready = False

        self.status_var = tk.StringVar(value="正在启动 BLE 扫描……")
        self.step_var = tk.StringVar(value="等待扫描器就绪")
        self.countdown_var = tk.StringVar(value="--")
        self.progress_var = tk.DoubleVar(value=0)

        self._build_ui()

        append_log("Cachito BLE guided scan v6 started")
        append_log(f"Output: {OUTPUT}")
        append_log("Model: 吮吸 0-100 / 炮机 0-100 / 嗨翻=重力感应")
        append_log("-" * 80)

        self.scanner = ScannerThread(self._scanner_status_from_thread)
        self.scanner.start()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer,
            text="Cachito BLE 引导测试",
            font=("Microsoft YaHei UI", 24, "bold"),
        )
        title.pack(pady=(0, 8))

        subtitle = ttk.Label(
            outer,
            text="iPhone 正常连接设备；电脑只负责计时、提示和记录广播",
            font=("Microsoft YaHei UI", 11),
        )
        subtitle.pack(pady=(0, 18))

        self.status_label = ttk.Label(
            outer,
            textvariable=self.status_var,
            font=("Microsoft YaHei UI", 11),
        )
        self.status_label.pack(pady=(0, 20))

        action_box = ttk.LabelFrame(outer, text="当前动作", padding=24)
        action_box.pack(fill="both", expand=True)

        self.action_label = ttk.Label(
            action_box,
            textvariable=self.step_var,
            anchor="center",
            justify="center",
            wraplength=760,
            font=("Microsoft YaHei UI", 23, "bold"),
        )
        self.action_label.pack(fill="both", expand=True, pady=(10, 16))

        self.countdown_label = ttk.Label(
            action_box,
            textvariable=self.countdown_var,
            anchor="center",
            font=("Segoe UI", 52, "bold"),
        )
        self.countdown_label.pack(pady=(0, 12))

        self.progress = ttk.Progressbar(
            action_box,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress.pack(fill="x", pady=(0, 12))

        self.step_counter = ttk.Label(
            action_box,
            text=f"共 {len(TEST_STEPS)} 步",
            anchor="center",
            font=("Microsoft YaHei UI", 11),
        )
        self.step_counter.pack()

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(22, 0))

        self.start_button = ttk.Button(
            buttons,
            text="开始完整测试",
            command=self.start_test,
            state="disabled",
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.pause_button = ttk.Button(
            buttons,
            text="暂停",
            command=self.toggle_pause,
            state="disabled",
        )
        self.pause_button.pack(side="left", padx=(0, 10))

        self.next_button = ttk.Button(
            buttons,
            text="已调好，开始采样",
            command=self.next_step,
            state="disabled",
        )
        self.next_button.pack(side="left", padx=(0, 10))

        self.stop_button = ttk.Button(
            buttons,
            text="结束并保存",
            command=self.finish_test,
            state="normal",
        )
        self.stop_button.pack(side="right")

        note = ttk.Label(
            outer,
            text=(
                "操作方式：先把 iPhone 滑块或姿态调到当前目标；"
                "调好后点击“已调好，开始采样”。调整过程不计入采样窗口。"
            ),
            wraplength=850,
            justify="center",
            font=("Microsoft YaHei UI", 10),
        )
        note.pack(pady=(16, 0))

    def _scanner_status_from_thread(self, message: str, is_error: bool) -> None:
        self.root.after(0, self._apply_scanner_status, message, is_error)

    def _apply_scanner_status(self, message: str, is_error: bool) -> None:
        self.status_var.set(message)

        if is_error:
            self.step_var.set("BLE 扫描启动失败")
            self.start_button.config(state="disabled")
            messagebox.showerror(
                "扫描失败",
                message + "\n\n请确认 Windows 蓝牙已开启，且电脑支持 BLE。",
            )
            return

        if message == "BLE 扫描已启动":
            self.scanner_ready = True
            self.step_var.set(
                "请先在 iPhone 打开 Cachito、连接设备，"
                "并将吮吸和炮机都设为暂停/0，关闭嗨翻。"
            )
            self.countdown_var.set("准备")
            self.start_button.config(state="normal")
            speak("蓝牙扫描已经启动。准备好后，点击开始完整测试。")

    def start_test(self) -> None:
        if not self.scanner_ready or self.running:
            return

        answer = messagebox.askokcancel(
            "开始测试",
            "请确认：\n\n"
            "1. iPhone 已连接设备\n"
            "2. 吮吸暂停/0\n"
            "3. 炮机暂停/0\n"
            "4. 嗨翻关闭\n"
            "5. 建议空载测试，并保留物理关机手段\n\n"
            "点击“确定”后开始。",
        )
        if not answer:
            return

        self.running = True
        self.paused = False
        self.phase = "prepare"
        self.current_step = -1
        self.start_button.config(state="disabled")
        self.pause_button.config(state="disabled", text="暂停")
        self.next_button.config(state="normal", text="已调好，开始采样")
        self.status_var.set("准备当前步骤；调整过程不会计入采样窗口")
        self._advance_step()

    def _advance_step(self) -> None:
        if not self.running:
            return

        self.current_step += 1
        if self.current_step >= len(TEST_STEPS):
            self.complete_test()
            return

        self.phase = "prepare"
        self.paused = False
        action, _ = TEST_STEPS[self.current_step]
        self.step_var.set(action)
        self.countdown_var.set("准备")
        self.progress_var.set(0)
        self.step_counter.config(
            text=f"第 {self.current_step + 1} / {len(TEST_STEPS)} 步"
        )
        self.status_var.set("请先调到目标状态；调好后再开始采样")
        self.pause_button.config(state="disabled", text="暂停")
        self.next_button.config(state="normal", text="已调好，开始采样")

        beep(1000, 180)
        speak(action + "。调好后，点击开始采样。")

    def _start_capture(self) -> None:
        if not self.running or self.phase != "prepare":
            return

        action, duration = TEST_STEPS[self.current_step]
        self.phase = "capture"
        self.paused = False
        self.remaining = duration

        # 允许稳定状态的下一次重复广播重新写入日志。
        last_seen.clear()

        now = datetime.now()
        append_log("")
        append_log(
            f"===== CAPTURE START {self.current_step + 1}/{len(TEST_STEPS)} | "
            f"{now:%Y-%m-%d %H:%M:%S.%f} | {duration}s | {action} ====="
        )

        if duration > 6:
            self.status_var.set("正在采样；请按提示完成移动")
            voice_prompt = "开始采样，请开始移动"
        else:
            self.status_var.set("正在采样；请保持当前状态")
            voice_prompt = "开始采样"
        self.countdown_var.set(str(duration))
        self.progress_var.set(0)
        self.next_button.config(state="disabled", text="已调好，开始采样")
        self.pause_button.config(state="normal", text="暂停")

        beep(1250, 220)
        speak(voice_prompt)
        self._tick()

    def _finish_capture(self) -> None:
        if not self.running or self.phase != "capture":
            return

        action, _ = TEST_STEPS[self.current_step]
        now = datetime.now()
        append_log(
            f"===== CAPTURE END {self.current_step + 1}/{len(TEST_STEPS)} | "
            f"{now:%Y-%m-%d %H:%M:%S.%f} | {action} ====="
        )

        self.progress_var.set(100)
        self.countdown_var.set("完成")
        self.pause_button.config(state="disabled", text="暂停")
        beep(1450, 180)
        speak("采样完成")
        self.phase = "between"
        self.timer_job = self.root.after(700, self._advance_step)

    def _tick(self) -> None:
        if not self.running or self.phase != "capture":
            return

        if self.paused:
            self.timer_job = self.root.after(250, self._tick)
            return

        _, total = TEST_STEPS[self.current_step]
        self.countdown_var.set(str(self.remaining))
        completed = (total - self.remaining) / total * 100
        self.progress_var.set(completed)

        if self.remaining <= 0:
            self._finish_capture()
            return

        if self.remaining <= 3:
            beep(700 + (4 - self.remaining) * 150, 100)

        self.remaining -= 1
        self.timer_job = self.root.after(1000, self._tick)

    def toggle_pause(self) -> None:
        if not self.running or self.phase != "capture":
            return

        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="继续")
            self.status_var.set("采样计时已暂停；BLE 仍在记录")
            speak("计时暂停")
        else:
            self.pause_button.config(text="暂停")
            self.status_var.set("正在采样；请保持当前状态")
            speak("继续")

    def next_step(self) -> None:
        if not self.running:
            return

        if self.phase == "prepare":
            self._start_capture()

    def finish_test(self) -> None:
        if self.running:
            answer = messagebox.askyesno(
                "提前结束",
                "测试还没有全部完成。确定结束并保存当前日志吗？",
            )
            if not answer:
                return

        self._stop_and_show_result("测试已结束，日志已保存")

    def complete_test(self) -> None:
        beep(1500, 250)
        beep(1800, 400)
        speak("测试完成")
        self._stop_and_show_result("全部测试完成，日志已保存")

    def _stop_and_show_result(self, status: str) -> None:
        if self.running and self.phase == "capture":
            action, _ = TEST_STEPS[self.current_step]
            append_log(
                f"===== CAPTURE ABORTED {self.current_step + 1}/{len(TEST_STEPS)} | "
                f"{datetime.now():%Y-%m-%d %H:%M:%S.%f} | {action} ====="
            )

        self.running = False
        self.paused = False
        self.phase = "finished"

        if self.timer_job:
            try:
                self.root.after_cancel(self.timer_job)
            except Exception:
                pass
            self.timer_job = None

        self.scanner.stop()

        append_log("")
        append_log(f"===== TEST FINISHED | {datetime.now():%Y-%m-%d %H:%M:%S.%f} =====")

        self.status_var.set(status)
        self.step_var.set("完成")
        self.countdown_var.set("✓")
        self.progress_var.set(100)

        self.start_button.config(state="disabled")
        self.pause_button.config(state="disabled")
        self.next_button.config(state="disabled")

        messagebox.showinfo(
            "完成",
            f"{status}\n\n日志位置：\n{OUTPUT}",
        )

    def close(self) -> None:
        if self.running:
            answer = messagebox.askyesno(
                "关闭程序",
                "测试仍在进行。确定关闭并保存当前日志吗？",
            )
            if not answer:
                return

        try:
            self.scanner.stop()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        error_path = Path(__file__).resolve().parent / "cachito-error.txt"
        error_path.write_text(
            f"{datetime.now():%Y-%m-%d %H:%M:%S}\n{type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        try:
            messagebox.showerror(
                "运行失败",
                f"{type(exc).__name__}: {exc}\n\n错误已保存到：\n{error_path}",
            )
        except Exception:
            pass
        raise
