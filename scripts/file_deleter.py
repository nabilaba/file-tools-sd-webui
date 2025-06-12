import os
import time
import mimetypes
import gradio as gr
from modules import script_callbacks

def list_root_folders():
    root_base = os.path.abspath(os.path.join(os.getcwd(), "models"))
    return sorted([f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))])

def get_file_details(folder):
    base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    if not os.path.isdir(base_path):
        return [], []

    rows = []
    choices = []
    for root, _, files in os.walk(base_path):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, base_path)
            size = os.path.getsize(full_path)
            ctime = os.path.getctime(full_path)
            mtime = os.path.getmtime(full_path)
            ftype, _ = mimetypes.guess_type(full_path)

            rows.append([
                fname,
                rel_path,
                f"{size / 1024:.2f} KB",
                ftype or "Unknown",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime)),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
            ])
            choices.append(rel_path)

    return rows, gr.update(choices=choices, value=[])

def delete_selected_files(folder, selected_paths):
    if not selected_paths:
        return "⚠️ Please select one or more files."

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

    rows, choices = get_file_details(folder)
    return message, rows, choices

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## 🗑️ File Deleter for Stable Diffusion WebUI")

        folder_dropdown = gr.Dropdown(
            choices=list_root_folders(),
            label="📁 Folder",
            interactive=True
        )

        file_multiselect = gr.CheckboxGroup(
            choices=[],
            label="📄 Select Files to Delete",
            interactive=True
        )

        file_table = gr.Dataframe(
            headers=["Name", "Relative Path", "Size", "Type", "Created", "Modified"],
            label="📊 File Details",
            interactive=False
        )

        delete_btn = gr.Button("❌ Delete Selected Files")
        status = gr.Textbox(label="📝 Status", lines=10, interactive=False)

        def update_ui(folder):
            rows, choices = get_file_details(folder)
            return rows, choices

        folder_dropdown.change(fn=update_ui, inputs=folder_dropdown, outputs=[file_table, file_multiselect])
        delete_btn.click(fn=delete_selected_files, inputs=[folder_dropdown, file_multiselect], outputs=[status, file_table, file_multiselect])

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
