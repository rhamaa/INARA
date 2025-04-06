import flet as ft
import os

def main(page: ft.Page):
    # Path ke file Markdown, relatif terhadap lokasi main.py
    md_file_path = os.path.join(os.path.dirname(__file__), "md", "main.md")
    
    # Baca konten dari file Markdown
    try:
        with open(md_file_path, "r", encoding="utf-8") as md_file:
            markdown_content = md_file.read()
    except Exception as e:
        markdown_content = f"# Error Membaca File Markdown\n\nTerjadi kesalahan saat membaca file: {str(e)}"
    
    page.scroll = "auto"
    page.add(
        ft.Markdown(
            markdown_content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: page.launch_url(e.data),
        )
    )

ft.app(main)