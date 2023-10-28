import requests
from time import sleep
from random import randint, uniform
import re
from PIL import Image
import os
from PyPDF2 import PdfWriter as PdfWriter, PdfReader


class Utils:
    def __init__(self, logger):
        self.logger = logger

    @staticmethod
    def parse_chapter_number(input_str):
        pattern = re.compile(
            r"(?:chapter|ch|issue|\/|\s|-|_)\s*(\d+(?:[\.-]\d+)?)", re.IGNORECASE
        )
        matches = pattern.findall(input_str)

        # Filter only those numbers which have preceding markers like "chapter", "ch" or "issue"
        filtered_matches = [
            m
            for m, full in [(m, f) for m in matches for f in input_str.split(m)]
            if "chapter" in full.lower()
            or "ch" in full.lower()
            or "issue" in full.lower()
        ]

        if filtered_matches:
            last_match = filtered_matches[-1]
            return (
                float(last_match.replace("-", "."))
                if ("." in last_match or "-" in last_match)
                else int(last_match)
            )
        elif matches:
            # If no filtered match is found, revert to the last found match as a fallback.
            last_match = matches[-1]
            return (
                float(last_match.replace("-", "."))
                if ("." in last_match or "-" in last_match)
                else int(last_match)
            )
        return None

    def make_request(
        self, url, return_bytes=False, max_retries=3, sleep_min=2, sleep_max=5
    ):
        retries = 0
        while retries < max_retries:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
                }
                response = requests.get(url, timeout=10, headers=headers)
                response.raise_for_status()
                # Random sleep between requests
                sleep(uniform(sleep_min, sleep_max))
                return response.content if return_bytes else response.text
            except requests.RequestException as e:
                retries += 1
                self.logger.error(
                    "HTTP request failed: %s. Retrying %s/%s", e, retries, max_retries
                )
                sleep(randint(5, 10))  # Sleep for a bit before retrying

        self.logger.error("Failed to retrieve data after %s attempts.", max_retries)
        return None

    @staticmethod
    def merge_images_to_pdf(chapter_path, pdf_name="merged"):
        if not os.path.exists(chapter_path):
            raise ValueError(f"Directory does not exist: {chapter_path}")
        if os.path.exists(os.path.join(chapter_path, f"{pdf_name}.pdf")):
            print(f"{pdf_name}.pdf already exists")
            return None

        image_files = [
            f for f in os.listdir(chapter_path) if f.endswith((".jpg", ".jpeg", ".png"))
        ]
        image_files.sort()
        if not image_files:
            print("No image files to merge.")
            return

        image_list = []
        for image_file in image_files:
            try:
                image = Image.open(os.path.join(chapter_path, image_file))
                image = image.convert("RGB")
                image_list.append(image)
            except OSError as e:
                print(f"Skipping {image_file}: {e}")

        if not image_list:
            print("No valid image files to merge.")
            return

        pdf_path = os.path.join(chapter_path, f"{pdf_name}.pdf")
        image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])


def merge_images_to_pdf(path, utils_instance):
    for _, dirnames, _ in os.walk(path):
        for dirname in dirnames:
            utils_instance.merge_images_to_pdf(
                os.path.join(path, dirname),
                dirname,
            )


def natural_sort_key(s):
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]


def merge_chapters_into_volumes(
    main_directory_path,
    covers_path,
    output_path,
    utils_instance,
    chapters_per_volume=12,
    start_volume_number=1,
):
    pdf_writer = PdfWriter()

    volume_number = start_volume_number
    chapter_count = 0
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Sort directories first
    dirnames = next(os.walk(main_directory_path))[1]
    sorted_dirnames = sorted(
        dirnames,
        key=lambda x: utils_instance.parse_chapter_number(x)
        if x.startswith("chapter_")
        else float("inf"),  # Any non-matching directory names go to the end
    )
    total_chapter_count = sum(
        len([f for f in files if f.endswith(".pdf") and f.startswith("chapter")])
        for _, _, files in os.walk(main_directory_path)
    )

    for dirname in sorted_dirnames:
        dirpath = os.path.join(main_directory_path, dirname)
        for _, _, filenames in os.walk(dirpath):
            for filename in sorted(
                [f for f in filenames if f.endswith(".pdf") and f.startswith("chapter")]
            ):
                chapter_count += 1
                print(
                    f"Processing {filename}, Chapter Count: {chapter_count}, Volume: {volume_number}, chapter_count % chapters_per_volume = {chapter_count % chapters_per_volume}"
                )

                # Your existing code to process each PDF
                pdf_reader = PdfReader(open(os.path.join(dirpath, filename), "rb"))

                # Add each page to the writer object
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)

                # If the required chapters per volume are reached, add a cover and save the PDF
                is_last_chapter = chapter_count == total_chapter_count
                should_create_pdf = (
                    chapter_count % chapters_per_volume == 0
                ) or is_last_chapter

                if should_create_pdf:
                    cover_image_path = os.path.join(covers_path, f"{volume_number}.jpg")

                    if os.path.exists(cover_image_path):
                        cover_image = Image.open(cover_image_path).convert("RGB")
                        cover_image.save("cover.pdf")
                        cover_pdf = PdfReader(open("cover.pdf", "rb"))

                        # Create a new PdfWriter object for rearranging pages
                        new_pdf_writer = PdfWriter()

                        # Add cover
                        new_pdf_writer.add_page(cover_pdf.pages[0])

                        # Add other pages
                        for page in pdf_writer.pages:
                            new_pdf_writer.add_page(page)

                        # Save the complete PDF (cover + chapters)

                        volume_pdf_path = os.path.join(
                            output_path, f"volume_{volume_number}.pdf"
                        )
                        with open(volume_pdf_path, "wb") as f_out:
                            new_pdf_writer.write(f_out)

                        # Increment the volume number
                        volume_number += 1

                        # Clean up and prepare for the next volume
                        pdf_writer = PdfWriter()
                    else:
                        print(
                            f"Cover image for volume {volume_number} not found. Skipping this volume."
                        )


if __name__ == "__main__":
    utils = Utils(logger=None)
    MAIN_DIRECTORY_PATH = "path/to/downloaded/manga"
    # merge_images_to_pdf(MAIN_DIRECTORY_PATH, utils)
    merge_chapters_into_volumes(
        main_directory_path=MAIN_DIRECTORY_PATH,
        output_path=os.path.join(MAIN_DIRECTORY_PATH, r"volumes"),
        covers_path=os.path.join(MAIN_DIRECTORY_PATH, r"covers"),
        chapters_per_volume=7,
        start_volume_number=1,
        utils_instance=utils,
    )
