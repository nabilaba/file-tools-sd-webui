import os
import time
import mimetypes
import gradio as gr
from modules import script_callbacks

def list_root_folders():
    root_base = os.path.abspath(os.path.join(os.getcwd(), "models"))
    return sorted([f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))])

def format_size(size_bytes):
    return f"{size_bytes / 1024:.2f} KB"

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

            # Filter by extension if specified
            if ext_filter != "All" and not fname.lower().endswith(ext_filter.lower()):
                continue

            size = os.path.getsize(full_path)
            total_size += size

            label = f"{rel_path} ({format_size(size)})"
            file_choices.append((label, rel_path))

    summary = f"📦 Total files: {len(file_choices)} — Total size: {format_size(total_size)}"
    return [label for label, _ in file_choices], summary, [rel for _, rel in file_choices]

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

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## 🗑️ File Deleter with Extension Filter & Size Summary")

        with gr.Row():
            folder_dropdown = gr.Dropdown(choices=list_root_folders(), label="📁 Folder", interactive=True)
            ext_dropdown = gr.Dropdown(choices=["All", ".ckpt", ".safetensors", ".pt", ".bin", ".pth"], label="🔍 Filter by Extension", value="All", interactive=True)

        file_checkbox = gr.CheckboxGroup(choices=[], label="☑️ Select Files (Relative Path + Size)", interactive=True)
        file_summary = gr.Textbox(label="📊 Total File Info", interactive=False)
        delete_btn = gr.Button("❌ Delete Selected Files")
        status_box = gr.Textbox(label="📝 Status", lines=10, interactive=False)

        hidden_all_rel_paths = gr.State([])  # internal use

        def update_files(folder, ext):
            labels, summary, rel_paths = get_file_details(folder, ext)
            return gr.update(choices=labels, value=[]), summary, rel_paths

        folder_dropdown.change(update_files, inputs=[folder_dropdown, ext_dropdown], outputs=[file_checkbox, file_summary, hidden_all_rel_paths])
        ext_dropdown.change(update_files, inputs=[folder_dropdown, ext_dropdown], outputs=[file_checkbox, file_summary, hidden_all_rel_paths])

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

        delete_btn.click(delete_handler, inputs=[folder_dropdown, file_checkbox, hidden_all_rel_paths], outputs=status_box)

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
