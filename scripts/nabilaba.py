import os
import shutil
import requests
from urllib.parse import urlparse, unquote
import gradio as gr
from modules import script_callbacks

def list_root_folders():
    root_base = os.path.abspath(os.path.join(os.getcwd(), "models"))
    os.makedirs(root_base, exist_ok=True)
    return sorted([f for f in os.listdir(root_base) if os.path.isdir(os.path.join(root_base, f))])

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

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

def perform_download(file_url_or_path, target_folder):
    try:
        base_folder = os.path.abspath(os.path.join(os.getcwd(), "models", target_folder))
        os.makedirs(base_folder, exist_ok=True)

        if file_url_or_path.startswith(("http://", "https://")):
            response = requests.get(file_url_or_path, stream=True)
            response.raise_for_status()

            content_disposition = response.headers.get("Content-Disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip('"')
            else:
                parsed_url = urlparse(file_url_or_path)
                filename = unquote(os.path.basename(parsed_url.path))

            dest_path = os.path.join(base_folder, filename)
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            return f"✅ Downloaded to: {dest_path}"

        if os.path.isfile(file_url_or_path):
            filename = os.path.basename(file_url_or_path)
            dest_path = os.path.join(base_folder, filename)
            shutil.copy(file_url_or_path, dest_path)
            return f"✅ Copied to: {dest_path}"

        return "❌ Error: File not found or invalid input."

    except Exception as e:
        return f"❌ Failed: {str(e)}"

def refresh_folders():
    return gr.update(choices=list_root_folders())

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
            status_box = gr.Textbox(label="🗘️ Status", lines=10, interactive=False)
            hidden_all_rel_paths = gr.State([])

            def update_files(folder, ext):
                labels, summary, rel_paths = get_file_details(folder, ext)
                return gr.update(choices=labels, value=[]), summary, rel_paths

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
                url_input = gr.Textbox(label="🔗 File URL or Path")
                save_to_folder = gr.Dropdown(choices=list_root_folders(), label="📁 Save To Folder")

            download_status = gr.Textbox(label="🛆 Status", lines=4, interactive=False)
            download_btn = gr.Button("⬇️ Start Download")

            save_to_folder.change(refresh_folders, outputs=save_to_folder)
            download_btn.click(
                perform_download,
                inputs=[url_input, save_to_folder],
                outputs=[download_status]
            )

    return [(combined_ui, "🧰 File Tools", "file_tools_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
