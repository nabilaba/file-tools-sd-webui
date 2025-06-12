import os
import time
import mimetypes
import requests
from urllib.parse import urlparse
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

def download_file(url, folder):
    if not url or not folder:
        yield gr.update(), gr.update(), "⚠️ Please provide both URL and folder"
        return

    dest_dir = os.path.abspath(os.path.join(os.getcwd(), "models", folder))
    os.makedirs(dest_dir, exist_ok=True)

    try:
        filename = os.path.basename(urlparse(url).path) or "downloaded_file"
        dest_path = os.path.join(dest_dir, filename)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        kb = downloaded / 1024
                        yield gr.update(), gr.update(), f"⬇️ Downloaded {kb:.2f} KB"

        yield gr.update(), gr.update(), f"✅ Completed: {filename}"
    except Exception as e:
        yield gr.update(), gr.update(), f"❌ Error: {e}"

def download_wrapper(url, folder):
    # Disable inputs at start
    yield gr.update(interactive=False), gr.update(interactive=False), "⏳ Starting download..."
    for update in download_file(url, folder):
        yield update
    # Re-enable inputs at end
    yield gr.update(interactive=True), gr.update(interactive=True), "✅ Ready for next download"

def on_ui_tabs():
    with gr.Blocks() as combined_ui:
        gr.Markdown("## 🧰 File Tools: Delete + Download")

        with gr.Tab("🗑️ Delete Files"):
            with gr.Row():
                folder_dropdown = gr.Dropdown(choices=list_root_folders(), label="📁 Folder", interactive=True)
                ext_dropdown = gr.Dropdown(choices=["All", ".ckpt", ".safetensors", ".pt", ".bin", ".pth"], label="🔍 Filter by Extension", value="All", interactive=True)

            file_checkbox = gr.CheckboxGroup(choices=[], label="☑️ Select Files (Relative Path + Size)", interactive=True)
            file_summary = gr.Textbox(label="📊 Total File Info", interactive=False)
            delete_btn = gr.Button("❌ Delete Selected Files")
            status_box = gr.Textbox(label="📝 Status", lines=10, interactive=False)
            hidden_all_rel_paths = gr.State([])

            def update_files(folder, ext):
                labels, summary, rel_paths = get_file_details(folder, ext)
                return gr.update(choices=labels, value=[]), summary, rel_paths

            def refresh_folders():
                return gr.update(choices=list_root_folders())

            folder_dropdown.change(update_files, inputs=[folder_dropdown, ext_dropdown], outputs=[file_checkbox, file_summary, hidden_all_rel_paths])
            ext_dropdown.change(update_files, inputs=[folder_dropdown, ext_dropdown], outputs=[file_checkbox, file_summary, hidden_all_rel_paths])
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

            delete_btn.click(delete_handler, inputs=[folder_dropdown, file_checkbox, hidden_all_rel_paths], outputs=status_box)

        with gr.Tab("⬇️ Download File"):
            with gr.Row():
                url_input = gr.Textbox(label="🔗 File URL")
                save_to_folder = gr.Dropdown(choices=list_root_folders(), label="📁 Save To Folder")

            download_status = gr.Textbox(label="📶 Progress", lines=6, interactive=False)
            download_btn = gr.Button("⬇️ Start Download")

            save_to_folder.change(refresh_folders, outputs=save_to_folder)
            download_btn.click(download_wrapper, inputs=[url_input, save_to_folder], outputs=[url_input, save_to_folder, download_status], queue=True)

    return [(combined_ui, "🧰 File Tools", "file_tools_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
