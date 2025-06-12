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
                fname,                               # File Name
                rel_path,                            # Relative Path
                f"{size / 1024:.2f} KB",             # Size
                ftype or "Unknown",                  # Type
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime)),  # Created
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))   # Modified
            ])
            choices.append(rel_path)

    return rows, gr.update(choices=choices, value=None)

def delete_multiple_and_refresh(folder, selected_rows):
    if not selected_rows or not isinstance(selected_rows, list):
        return "⚠️ Please select one or more rows from the table.", gr.update(), gr.update()

    deleted_files = []
    errors = []

    for row in selected_rows:
        if len(row) < 2:
            continue
        rel_path = row[1]  # 2nd column = relative path
        base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
        file_path = os.path.join(base_path, rel_path)
        try:
            os.remove(file_path)
            deleted_files.append(rel_path)
        except Exception as e:
            errors.append(f"{rel_path} → ❌ {e}")

    msg = ""
    if deleted_files:
        msg += "✅ Deleted:\n" + "\n".join(deleted_files)
    if errors:
        msg += "\n\n⚠️ Errors:\n" + "\n".join(errors)
    if not deleted_files and not errors:
        msg = "⚠️ No valid files selected."

    rows, file_list = get_file_details(folder)
    return msg, rows, gr.update(choices=file_list, value=None)

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## 🗑️ File Deleter with Details")

        folder_dropdown = gr.Dropdown(
            choices=list_root_folders(),
            label="📁 Folder (from models)",
            interactive=True
        )

        status = gr.Textbox(label="📝 Status", lines=10, interactive=False)

        file_table = gr.Dataframe(
            headers=["Name", "Relative Path", "Size", "Type", "Created", "Modified"],
            label="📊 File Details (select multiple rows)",
            interactive=True,
            row_selectable="multi",
            wrap=True,
            visible=True
        )

        delete_btn = gr.Button("❌ Delete Selected Files")

        # When folder is selected, update file list and dropdown
        def update_ui(folder):
            rows, file_list = get_file_details(folder)
            return rows, file_list

        folder_dropdown.change(
            fn=update_ui,
            inputs=folder_dropdown,
            outputs=[file_table, gr.update()]
        )

        delete_btn.click(
            fn=delete_multiple_and_refresh,
            inputs=[folder_dropdown, file_table],
            outputs=[status, file_table, gr.update()]
        )

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
