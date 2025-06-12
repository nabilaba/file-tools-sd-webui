import os
import time
import mimetypes
import gradio as gr
from modules import script_callbacks

def list_root_folders():
    root_base = os.path.abspath(os.path.join(os.getcwd(), "models"))
    return sorted([f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))])

def format_size(bytes_val):
    return f"{bytes_val / 1024 / 1024:.2f} MB" if bytes_val > 1024 * 1024 else f"{bytes_val / 1024:.2f} KB"

def get_file_details_for_checkbox(folder, ext_filter):
    base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    if not os.path.isdir(base_path):
        return gr.update(choices=[], value=[]), gr.update(value="")

    checkbox_labels = []
    total_size = 0
    total_files = 0

    for root, _, files in os.walk(base_path):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, base_path)
            size = os.path.getsize(full_path)
            ftype, _ = mimetypes.guess_type(full_path)

            # Filter by extension
            if ext_filter != "All" and not fname.endswith(ext_filter):
                continue

            ctime = os.path.getctime(full_path)
            mtime = os.path.getmtime(full_path)

            label = (
                f"📄 {fname}\n\n"
                f"Relative Path: {rel_path}\n"
                f"Size: {format_size(size)}\n"
                f"Type: {ftype or 'Unknown'}\n"
                f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))}\n"
                f"Modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}"
            )

            checkbox_labels.append((label, rel_path))
            total_size += size
            total_files += 1

    total_info = f"📦 Total files: {total_files} — Total size: {format_size(total_size)}"
    return gr.update(choices=checkbox_labels, value=[]), gr.update(value=total_info)

def delete_selected_files(folder, selected_paths, ext_filter):
    if not selected_paths:
        return "⚠️ Please select one or more files.", *get_file_details_for_checkbox(folder, ext_filter)

    base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    deleted, errors = [], []

    for rel_path in selected_paths:
        file_path = os.path.join(base_path, rel_path)
        try:
            os.remove(file_path)
            deleted.append(rel_path)
        except Exception as e:
            errors.append(f"{rel_path} → ❌ {e}")

    message = ""
    if deleted:
        message += "✅ Deleted:\n" + "\n".join(deleted)
    if errors:
        message += "\n\n⚠️ Errors:\n" + "\n".join(errors)
    if not deleted and not errors:
        message = "⚠️ No valid files selected."

    return message, *get_file_details_for_checkbox(folder, ext_filter)

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## 🗑️ File Deleter with Extension Filter & Size Summary")

        with gr.Row():
            folder_dropdown = gr.Dropdown(
                choices=list_root_folders(),
                label="📁 Folder",
                interactive=True
            )
            ext_filter_dropdown = gr.Dropdown(
                choices=["All", ".ckpt", ".safetensors", ".txt", ".bin", ".pt"],
                label="🔍 Filter by Extension",
                value="All",
                interactive=True
            )

        file_checkbox = gr.CheckboxGroup(
            choices=[],
            label="📄 Select Files (Details in Label)",
            interactive=True
        )

        total_info = gr.Textbox(label="📊 Total File Info", interactive=False)

        delete_btn = gr.Button("❌ Delete Selected Files")
        status = gr.Textbox(label="📝 Status", lines=10, interactive=False)

        # Update checkbox + total when folder/ext changed
        def refresh(folder, ext_filter):
            return get_file_details_for_checkbox(folder, ext_filter)

        folder_dropdown.change(fn=refresh, inputs=[folder_dropdown, ext_filter_dropdown], outputs=[file_checkbox, total_info])
        ext_filter_dropdown.change(fn=refresh, inputs=[folder_dropdown, ext_filter_dropdown], outputs=[file_checkbox, total_info])

        # Delete
        delete_btn.click(fn=delete_selected_files, inputs=[folder_dropdown, file_checkbox, ext_filter_dropdown], outputs=[status, file_checkbox, total_info])

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
