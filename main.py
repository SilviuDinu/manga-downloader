import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
import ast
import threading
from MangaScraper import MangaScraper


class TextHandler(logging.Handler):
    def __init__(self, text, root):
        super().__init__()
        self.text = text
        self.root = root

    def emit(self, record):
        msg = self.format(record)
        self.root.after(0, self.append_text, msg)

    def append_text(self, msg):
        self.text.configure(state="normal")
        self.text.insert(tk.END, msg + "\n")
        self.text.configure(state="disabled")
        self.text.yview(tk.END)


class MangaScraperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.root.title("Manga Scraper")
        self.entries = {}
        self.manga_scraper = None
        self.ui_elements = [
            {"text": "Start Chapter:", "widget_class": ttk.Entry},
            {"text": "End Chapter:", "widget_class": ttk.Entry},
            {"text": "Manga Title*:", "widget_class": ttk.Entry},
            {"text": "Main URL*:", "widget_class": ttk.Entry},
            {"text": "Chapter Link Selector*:", "widget_class": ttk.Entry},
            {"text": "Chapter Page Selector*:", "widget_class": ttk.Entry},
            {
                "text": 'Alternative Chapter Page Selector ["selector1", "selector2", ...]:',
                "widget_class": ttk.Entry,
            },
            {
                "text": "Merge images into PDF for each chapter",
                "widget_class": ttk.Checkbutton,
            },
            {
                "text": "Start Scraping",
                "widget_class": ttk.Button,
                "command": self.start_thread,
            },
        ]

    def setup_gui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root["padx"] = 20
        self.root["pady"] = 20

        row = 0
        for config in self.ui_elements:
            widget, var = self.create_ui_element(self.root, row, config)
            self.entries[config["text"]] = {"widget": widget, "var": var}
            row += 1

        self.root.grid_rowconfigure(len(self.ui_elements) + 1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.grid_rowconfigure(9, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        log_frame = tk.Frame(self.root)
        log_frame.grid(row=9, columnspan=2, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)

        handler = TextHandler(text, self.root)
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        self.manga_scraper = MangaScraper(logger)

    def create_ui_element(self, root, row, config):
        vertical_padding = 5
        horizontal_entry_width = 40  # Default width for Entry widgets

        widget_class = config["widget_class"]
        widget_kwargs = {"text": config.get("text", "")}

        if "command" in config:
            widget_kwargs["command"] = config["command"]

        # Create Label only if the widget is not a Button
        if widget_class != ttk.Button:
            ttk.Label(root, text=config["text"]).grid(
                row=row, column=0, sticky="w", pady=vertical_padding
            )
            widget = widget_class(root)
            widget.grid(row=row, column=1, sticky="e", pady=vertical_padding)
        else:
            widget = widget_class(root, **widget_kwargs)
            widget.grid(row=row, columnspan=2, pady=vertical_padding)

        # Additional configuration for specific widget types
        if widget_class == ttk.Entry:
            widget["width"] = config.get("width", horizontal_entry_width)
        elif widget_class == ttk.Checkbutton:
            var = tk.BooleanVar()
            widget["variable"] = var
            return widget, var

        return widget, None

    def run(self):
        self.setup_gui()
        self.root.mainloop()

    def get_entry_value(self, key):
        entry = self.entries.get(key, {})
        widget = entry.get("widget")
        return widget.get() if widget else None

    def validate_alternative_selector(self, raw_value):
        if not raw_value:
            return []

        selectors = ast.literal_eval(raw_value)

        if not isinstance(selectors, list):
            raise ValueError(
                "Expected a list of strings for the Alternative Selectors."
            )

        return selectors

    def start_thread(self):
        start_ch = self.get_entry_value("Start Chapter:") or None
        end_ch = self.get_entry_value("End Chapter:") or None
        manga_title = self.get_entry_value("Manga Title*:") or "Unknown Manga"
        main_url = self.get_entry_value("Main URL*:")
        chapter_page_selector = self.get_entry_value("Chapter Page Selector*:")
        chapter_link_selector = self.get_entry_value("Chapter Link Selector*:")
        merge_images_into_pdf = (
            self.entries["Merge images into PDF for each chapter"]["var"].get() or False
        )

        raw_alternative_selector = self.get_entry_value(
            'Alternative Chapter Page Selector ["selector1", "selector2", ...]:'
        )
        alternative_chapter_page_selector = self.validate_alternative_selector(
            raw_alternative_selector
        )

        args = (
            start_ch,
            end_ch,
            manga_title,
            main_url,
            chapter_page_selector,
            chapter_link_selector,
            alternative_chapter_page_selector,
            merge_images_into_pdf,
        )

        # Start the scraping thread
        scraping_thread = threading.Thread(
            target=self.manga_scraper.start_scraping, args=args
        )

        scraping_thread.start()


if __name__ == "__main__":
    app = MangaScraperApp()
    app.run()
