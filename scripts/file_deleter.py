import os
import gradio as gr
from modules import script_callbacks, shared

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## File Deleter")

        # Automatically list all root folders under webui root (one level only)
        root_base = os.getcwd()
        root_folders = [f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))]
        folder = gr.Dropdown(choices=sorted(root_folders), label="Folder (Auto-detected from root)")

        file = gr.Dropdown(choices=[], label="File (including subfolders)", multiselect=False)
        delete = gr.Button("Delete")
        status = gr.Textbox(label="Status")

        def update_files(folder):
            base_path = os.path.abspath(os.path.join(shared.script_path, os.pardir, folder))
            if not os.path.isdir(base_path):
                return []
            file_list = []
            for root, _, files in os.walk(base_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, base_path)
                    file_list.append(rel_path)
            return sorted(file_list)

        def delete_file(folder, rel_path):
            if isinstance(rel_path, list):
                rel_path = rel_path[0]  # support single-selection
            base_path = os.path.abspath(os.path.join(shared.script_path, os.pardir, folder))
            file_path = os.path.join(base_path, rel_path)
            if not os.path.isfile(file_path):
                return "❌ File not found"
            try:
                os.remove(file_path)
                return f"✅ Deleted: {rel_path}"
            except Exception as e:
                return f"❌ Error deleting: {e}"

        folder.change(update_files, folder, file)
        delete.click(delete_file, inputs=[folder, file], outputs=status)

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
