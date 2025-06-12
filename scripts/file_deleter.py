import os
import gradio as gr
from modules import scripts, script_callbacks, shared

class FileDeleter(scripts.Script):
    def title(self): return "File Deleter"
    def show(self, is_img2img): return scripts.AlwaysVisible

    def ui(self, is_img2img):
        folder_choices = ["models", "models/Stable-diffusion", "extensions", "loras", "embeddings"]
        folder = gr.Dropdown(choices=folder_choices, label="Folder")
        file = gr.Dropdown(choices=[], label="File")
        delete = gr.Button("Delete")
        status = gr.Textbox(label="Status")

        folder.change(self.update_files, folder, file)
        delete.click(self.delete_file, inputs=[folder, file], outputs=status)

        return [folder, file, delete, status]

    def update_files(self, folder):
        p = os.path.join(shared.script_path, os.pardir, folder)
        if not os.path.isdir(p): return []
        return sorted(os.listdir(p))

    def delete_file(self, folder, filename):
        p = os.path.join(shared.script_path, os.pardir, folder, filename)
        if not os.path.isfile(p):
            return "❌ File not found"
        try:
            os.remove(p)
            return f"✅ Deleted: {filename}"
        except Exception as e:
            return f"❌ Error deleting: {e}"

def on_ui_tabs():
    file_deleter = FileDeleter()
    return (gr.Blocks(title="File Deleter"), "File Deleter", "file_deleter_tab")

script_callbacks.on_ui_tabs(on_ui_tabs)
