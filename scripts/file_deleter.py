import os
import gradio as gr
from modules import scripts, script_callbacks, shared

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## File Deleter")
        folder_choices = ["models", "models/Stable-diffusion", "extensions", "loras", "embeddings"]
        folder = gr.Dropdown(choices=folder_choices, label="Folder")
        file = gr.Dropdown(choices=[], label="File")
        delete = gr.Button("Delete")
        status = gr.Textbox(label="Status")

        def update_files(folder):
            p = os.path.join(shared.script_path, os.pardir, folder)
            return sorted(os.listdir(p)) if os.path.isdir(p) else []

        def delete_file(folder, filename):
            p = os.path.join(shared.script_path, os.pardir, folder, filename)
            if not os.path.isfile(p): return "❌ File not found"
            try:
                os.remove(p)
                return f"✅ Deleted: {filename}"
            except Exception as e:
                return f"❌ Error deleting: {e}"

        folder.change(update_files, folder, file)
        delete.click(delete_file, inputs=[folder, file], outputs=status)

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
