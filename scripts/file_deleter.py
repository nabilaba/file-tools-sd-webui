import os
import gradio as gr
from modules import script_callbacks

def on_ui_tabs():
    with gr.Blocks() as file_deleter_ui:
        gr.Markdown("## File Deleter")

        # Deteksi folder di root
        root_base = os.getcwd()
        root_folders = [f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))]
        folder = gr.Dropdown(choices=sorted(root_folders), label="Folder (Auto-detected from root)", interactive=True)

        file = gr.Dropdown(choices=[], label="File (including subfolders)", multiselect=False, interactive=True)
        delete = gr.Button("Delete")
        status = gr.Textbox(label="Status", interactive=False)

        # Tabel detail file
        file_info = gr.Dataframe(headers=["Attribute", "Value"], visible=False, row_count=6, col_count=2, wrap=True)

        def update_files(folder):
            base_path = os.path.abspath(os.path.join(os.getcwd(), folder))
            if not os.path.isdir(base_path):
                return []
            file_list = []
            for root, _, files in os.walk(base_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, base_path)
                    file_list.append(rel_path)
            return sorted(file_list)

        def show_file_info(folder, rel_path):
            if not rel_path:
                return gr.update(visible=False), []

            base_path = os.path.abspath(os.path.join(os.getcwd(), folder))
            file_path = os.path.join(base_path, rel_path)

            if not os.path.isfile(file_path):
                return gr.update(visible=False), []

            stat = os.stat(file_path)
            file_data = [
                ["Name", os.path.basename(file_path)],
                ["Full Path", file_path],
                ["Size (KB)", round(stat.st_size / 1024, 2)],
                ["Type", os.path.splitext(file_path)[1]],
                ["Modified", format_time(stat.st_mtime)],
            ]
            return gr.update(visible=True), file_data

        def format_time(timestamp):
            import datetime
            return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        def delete_file(folder, rel_path):
            if not rel_path:
                return "⚠️ Please select a file to delete.", gr.update(visible=False), []

            base_path = os.path.abspath(os.path.join(os.getcwd(), folder))
            file_path = os.path.join(base_path, rel_path)

            if not os.path.isfile(file_path):
                return f"❌ File not found: {rel_path}", gr.update(visible=False), []

            try:
                os.remove(file_path)
                return f"✅ Deleted: {rel_path}", gr.update(visible=False), []
            except Exception as e:
                return f"❌ Error deleting: {e}", gr.update(visible=False), []

        # Events
        folder.change(update_files, folder, file)
        file.change(show_file_info, inputs=[folder, file], outputs=[file_info, file_info])
        delete.click(delete_file, inputs=[folder, file], outputs=[status, file_info, file_info])

    return [(file_deleter_ui, "File Deleter", "file_deleter_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
