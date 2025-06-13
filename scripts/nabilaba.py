import os
import shutil
import requests
from urllib.parse import urlparse, unquote
import gradio as gr
from modules import script_callbacks, sysinfo
import psutil


def list_root_folders():
    root_base = os.path.abspath(os.path.join(os.getcwd(), "models"))
    os.makedirs(root_base, exist_ok=True)
    return sorted(
        [f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))]
    )


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def get_file_details(folder, ext_filter):
    base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    if not os.path.isdir(base_path):
        return [], "", []

    file_choices = []
    total_size = 0
    for root, _, files in os.walk(base_path):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, base_path)

            if ext_filter != "All" and not fname.lower().endswith(ext_filter.lower()):
                continue

            size = os.path.getsize(full_path)
            total_size += size
            label = f"{rel_path} ({format_size(size)})"
            file_choices.append((label, rel_path))

    summary = (
        f"📦 Total files: {len(file_choices)} — Total size: {format_size(total_size)}"
    )
    return (
        [label for label, _ in file_choices],
        summary,
        [rel for _, rel in file_choices],
    )


def delete_selected_files(folder, selected_files):
    if not selected_files:
        return "⚠️ Please select files to delete."

    base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    messages = []

    for rel_path in selected_files:
        file_path = os.path.join(base_path, rel_path)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                messages.append(f"✅ Deleted: {rel_path}")
            except Exception as e:
                messages.append(f"❌ Error deleting {rel_path}: {e}")
        else:
            messages.append(f"❌ Not found: {rel_path}")

    return "\n".join(messages)


def perform_download(file_url_or_path, target_folder):
    try:
        base_folder = os.path.abspath(
            os.path.join(os.getcwd(), "models", target_folder)
        )
        os.makedirs(base_folder, exist_ok=True)

        if file_url_or_path.startswith(("http://", "https://")):
            response = requests.get(file_url_or_path, stream=True)
            response.raise_for_status()

            content_disposition = response.headers.get("Content-Disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip('"')
            else:
                parsed_url = urlparse(file_url_or_path)
                filename = unquote(os.path.basename(parsed_url.path))

            dest_path = os.path.join(base_folder, filename)
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            return f"✅ Downloaded to: {dest_path}"

        if os.path.isfile(file_url_or_path):
            filename = os.path.basename(file_url_or_path)
            dest_path = os.path.join(base_folder, filename)
            shutil.copy(file_url_or_path, dest_path)
            return f"✅ Copied to: {dest_path}"

        return "❌ Error: File not found or invalid input."

    except Exception as e:
        return f"❌ Failed: {str(e)}"


def refresh_folders():
    return gr.update(choices=list_root_folders())


def get_uptime():
    try:
        import time

        uptime_seconds = time.time() - psutil.boot_time()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"⏱️ Uptime: {days}d {hours}h {minutes}m"
    except Exception as e:
        return f"⚠️ Uptime error: {e}"


def get_storage_info():
    total, used, free = shutil.disk_usage(os.getcwd())
    return (
        f"💽 Total Storage: {format_size(total)}\n"
        f"📂 Used: {format_size(used)}\n"
        f"📭 Free: {format_size(free)}"
    )


def format_ram_info():
    try:
        ram = sysinfo.get_dict().get("RAM", {})

        # Define icons
        icon_map = {
            "total": "🧠",
            "used": "📊",
            "free": "🟢",
            "active": "🔄",
            "inactive": "💤",
            "buffers": "🗂️",
            "cached": "🧾",
            "shared": "🤝",
        }

        # Left and right column fields
        left_keys = ["total", "used", "free", "active"]
        right_keys = ["inactive", "buffers", "cached", "shared"]

        left_lines = []
        right_lines = []

        for key in left_keys:
            if key in ram:
                icon = icon_map.get(key, "🔹")
                label = key.capitalize()
                left_lines.append(f"{icon} {label}: {ram[key]}")

        for key in right_keys:
            if key in ram:
                icon = icon_map.get(key, "🔹")
                label = key.capitalize()
                right_lines.append(f"{icon} {label}: {ram[key]}")

        # Pad both columns to same length
        max_len = max(len(left_lines), len(right_lines))
        left_lines += [""] * (max_len - len(left_lines))
        right_lines += [""] * (max_len - len(right_lines))

        # Combine with padding
        output_lines = []
        for l, r in zip(left_lines, right_lines):
            output_lines.append(f"{l:<30} {r}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"❌ Error getting RAM info: {e}"


def format_cpu_info():
    try:
        data = sysinfo.get_dict()
        cpu_info = data.get("CPU", {})
        torch_cpu_lines = data.get("Torch env info", {}).get("cpu_info", [])

        # Left side fields
        wanted_left = {
            "Architecture:": "🏗️ Architecture",
            "CPU op-mode(s):": "🧮 Modes",
            "Vendor ID:": "🏢 Vendor",
        }

        # Right side fields
        right_lines = []

        # Get model name
        for line in torch_cpu_lines:
            if line.strip().startswith("Model name:"):
                model_value = line.split(":", 1)[1].strip()
                right_lines.append(f"🛠️ Model: {model_value}")
                break

        # Add logical & physical cores
        logical = cpu_info.get("count logical", "N/A")
        physical = cpu_info.get("count physical", "N/A")
        right_lines.append(f"🔣 Logical Cores: {logical}")
        right_lines.append(f"⚙️ Physical Cores: {physical}")

        # Left side info
        left_lines = []
        for line in torch_cpu_lines:
            for key, label in wanted_left.items():
                if line.strip().startswith(key):
                    value = line.split(":", 1)[1].strip()
                    left_lines.append(f"{label}: {value}")

        # Pad to equal lengths
        max_len = max(len(left_lines), len(right_lines))
        left_lines += [""] * (max_len - len(left_lines))
        right_lines += [""] * (max_len - len(right_lines))

        # Format 2-column layout
        output = []
        for l, r in zip(left_lines, right_lines):
            output.append(f"{l:<35} {r}")
        return "\n".join(output)

    except Exception as e:
        return f"❌ Error getting CPU info: {e}"


def format_gpu_info():
    try:
        from pynvml import (
            nvmlInit,
            nvmlShutdown,
            nvmlDeviceGetCount,
            nvmlDeviceGetHandleByIndex,
            nvmlDeviceGetName,
            nvmlDeviceGetMemoryInfo,
        )

        nvmlInit()
        lines = []
        device_count = nvmlDeviceGetCount()
        for i in range(device_count):
            handle = nvmlDeviceGetHandleByIndex(i)
            name = nvmlDeviceGetName(handle).decode()
            mem = nvmlDeviceGetMemoryInfo(handle)
            total = mem.total / (1024**2)
            used = mem.used / (1024**2)
            free = mem.free / (1024**2)
            lines.append(
                f"🎮 GPU {i}: {name}\n"
                f"   💾 Total: {total:.0f} MB | 📊 Used: {used:.0f} MB | 🟢 Free: {free:.0f} MB"
            )

        nvmlShutdown()
        return "\n".join(lines)

    except Exception as e:
        return f"⚠️ Unable to read GPU info: {e}"


def on_ui_tabs():
    with gr.Blocks() as combined_ui:
        gr.Markdown("## 🧰 File Tools")

        with gr.Tab("💾 Simple Info"):
            uptime_box = gr.Textbox(label="⏱️ System Uptime", interactive=False)
            uptime_box.value = get_uptime()

            storage_info = gr.Textbox(label="💡 Storage Usage", interactive=False)
            storage_info.value = get_storage_info()

            ram_info_box = gr.Textbox(label="🧠 RAM Status", interactive=False)
            ram_info_box.value = format_ram_info()

            cpu_box = gr.Textbox(label="🖥️ CPU Details", lines=8, interactive=False)
            cpu_box.value = format_cpu_info()

            gpu_info_box = gr.Textbox(
                label="🧠 GPU Detected", lines=5, interactive=False
            )
            gpu_info_box.value = format_gpu_info()

            refresh_btn = gr.Button("🔄 Refresh Info")

            def refresh_all_info():
                return (
                    get_storage_info(),
                    format_ram_info(),
                    format_cpu_info(),
                    format_gpu_info(),
                    get_uptime(),
                )

            refresh_btn.click(
                fn=refresh_all_info,
                outputs=[storage_info, ram_info_box, cpu_box, gpu_info_box, uptime_box],
            )

        with gr.Tab("🗑️ Delete Files"):
            with gr.Row():
                folder_dropdown = gr.Dropdown(
                    choices=list_root_folders(), label="📁 Folder", interactive=True
                )
                ext_dropdown = gr.Dropdown(
                    choices=["All", ".ckpt", ".safetensors", ".pt", ".bin", ".pth"],
                    label="🔍 Filter by Extension",
                    value="All",
                    interactive=True,
                )

            file_summary = gr.Textbox(label="📊 Total File Info", interactive=False)
            file_checkbox = gr.CheckboxGroup(
                choices=[],
                label="☑️ Select Files (Relative Path + Size)",
                interactive=True,
            )
            delete_btn = gr.Button("❌ Delete Selected Files")
            status_box = gr.Textbox(label="🗘️ Status", lines=10, interactive=False)
            hidden_all_rel_paths = gr.State([])

            def update_files(folder, ext):
                labels, summary, rel_paths = get_file_details(folder, ext)
                return gr.update(choices=labels, value=[]), summary, rel_paths

            folder_dropdown.change(
                update_files,
                inputs=[folder_dropdown, ext_dropdown],
                outputs=[file_checkbox, file_summary, hidden_all_rel_paths],
            )
            ext_dropdown.change(
                update_files,
                inputs=[folder_dropdown, ext_dropdown],
                outputs=[file_checkbox, file_summary, hidden_all_rel_paths],
            )
            folder_dropdown.change(refresh_folders, outputs=folder_dropdown)

            def map_labels_to_rel_paths(selected_labels, all_rel_paths):
                selected_paths = []
                for label in selected_labels:
                    for path in all_rel_paths:
                        if label.startswith(path):
                            selected_paths.append(path)
                            break
                return selected_paths

            def delete_handler(folder, selected_labels, all_paths):
                selected_paths = map_labels_to_rel_paths(selected_labels, all_paths)
                return delete_selected_files(folder, selected_paths)

            delete_btn.click(
                delete_handler,
                inputs=[folder_dropdown, file_checkbox, hidden_all_rel_paths],
                outputs=status_box,
            )

        with gr.Tab("⬇️ Download File"):
            with gr.Row():
                url_input = gr.Textbox(label="🔗 File URL or Path")
                save_to_folder = gr.Dropdown(
                    choices=list_root_folders(), label="📁 Save To Folder"
                )

            download_status = gr.Textbox(label="🛆 Status", lines=4, interactive=False)
            download_btn = gr.Button("⬇️ Start Download")

            save_to_folder.change(refresh_folders, outputs=save_to_folder)
            download_btn.click(
                perform_download,
                inputs=[url_input, save_to_folder],
                outputs=[download_status],
            )

    return [(combined_ui, "🧰 File Tools", "file_tools_tab")]


script_callbacks.on_ui_tabs(on_ui_tabs)
