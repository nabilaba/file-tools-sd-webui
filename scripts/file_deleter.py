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

def delete_file(folder, rel_path):
    if not rel_path:
        return "⚠️ Please select a file."
    base_path = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    file_path = os.path.join(base_path, rel_path)
    if not os.path.isfile(file_path):
        return f"❌ File not found: {rel_path}"
    try:
        os.remove(file_path)
        return f"✅ Deleted: {rel_path}"
    except Exception as e:
        return f"❌ Error: {e}"

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## 🗑️ File Deleter with Details")

        with gr.Row():
            folder_dropdown = gr.Dropdown(
                choices=list_root_folders(),
                label="📁 Folder (from root)",
                interactive=True
            )

            file_dropdown = gr.Dropdown(
                choices=[],
                label="📄 File to Delete (from list)",
                interactive=True
            )

        delete_btn = gr.Button("❌ Delete Selected File")
        status = gr.Textbox(label="📝 Status", interactive=False)

        file_table = gr.Dataframe(
            headers=["Name", "Relative Path", "Size", "Type", "Created", "Modified"],
            label="📊 File Details",
            interactive=False,
            wrap=True,
            visible=True
        )

        # When folder selected, populate files + table
        def update_ui(folder):
            rows, file_list = get_file_details(folder)
            return rows, file_list

        folder_dropdown.change(fn=update_ui, inputs=folder_dropdown, outputs=[file_table, file_dropdown])
        delete_btn.click(fn=delete_file, inputs=[folder_dropdown, file_dropdown], outputs=status)

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
