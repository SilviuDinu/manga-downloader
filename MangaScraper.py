import traceback
import os
from bs4 import BeautifulSoup
from Utils import Utils


class MangaScraper:
    def __init__(self, logger):
        self.logger = logger
        self.utils = Utils(logger)

    def download_files(
        self,
        url,
        current_ch,
        directory,
        chapter_page_selector,
        alternative_page_selectors,
    ):
        page_content = self.utils.make_request(url)
        if page_content is None:
            return
        image_urls = []
        self.logger.info("Downloading Chapter %s from %s...", current_ch, url)
        soup = BeautifulSoup(page_content, "html.parser")
        pages = soup.select(chapter_page_selector)
        if len(pages) == 0 and len(alternative_page_selectors) > 0:
            for alternative_selector in alternative_page_selectors:
                self.logger.info(
                    "Trying alternative selector %s from %s",
                    alternative_selector,
                    alternative_page_selectors,
                )
                pages = soup.select(alternative_selector)
                if len(pages) > 0:
                    break
        if not os.path.exists(directory):
            os.makedirs(directory)
        if len(pages) == 0:
            return
        for page in pages:
            image_url = page.get("src", None)
            if not image_url.startswith("http"):
                image_url = page.get("data-lazy-src", None)
            if not image_url in image_urls:
                image_urls.append(image_url)
        self.logger.info("Found %s pages for Chapter %s", len(image_urls), current_ch)
        self.logger.info("\rDownloading %s images", len(image_urls))
        for index, image_url in enumerate(image_urls):
            page_path = f"{directory}/{'0' + str(index) if index < 10 else index}.jpg"
            if os.path.exists(page_path) or os.path.exists(f"{directory}/{index}.jpg"):
                self.logger.info("Image %s already found. Skipping...", page_path)
                continue
            if image_url:
                try:
                    page_response = self.utils.make_request(
                        image_url, return_bytes=True
                    )
                    if page_response:
                        with open(page_path, "wb") as f:
                            f.write(page_response)
                except Exception as e:
                    self.logger.error(
                        "Error while downloading image %s / %s - Chapter %s: %s\n%s",
                        index + 1,
                        len(pages),
                        current_ch,
                        e,
                        traceback.format_exc(),
                    )

    def start_scraping(self, *args):
        (
            start_ch,
            end_ch,
            manga_title,
            main_url,
            chapter_page_selector,
            chapter_link_selector,
            alternative_chapter_page_selector,
            merge_images_into_pdf,
        ) = args

        self.logger.info(
            f"User-provided variables:\n"
            f"START_CH: {start_ch}\n"
            f"END_CH: {end_ch}\n"
            f"MANGA_TITLE: {manga_title}\n"
            f"main_url: {main_url}\n"
            f"CHAPTER_PAGE_SELECTOR: {chapter_page_selector}\n"
            f"chapter_link_selector: {chapter_link_selector}\n"
            f"ALTERNATIVE_CHAPTER_PAGE_SELECTOR: {alternative_chapter_page_selector}\n"
        )

        try:
            self.logger.info("Getting Chapters from %s ...", main_url)
            main_page_content = self.utils.make_request(main_url)
            if main_page_content:
                soup = BeautifulSoup(main_page_content, "html.parser")
                chapters = soup.select(chapter_link_selector)
                if chapters:
                    chapters.reverse()
                    self.logger.info(
                        f"Found {len(chapters)} chapters for {manga_title}"
                    )

                    start_ch_index = 0
                    # Initialize with the total number of chapters
                    end_ch_index = len(chapters)

                    if start_ch is not None:
                        for i, chapter in enumerate(chapters):
                            chapter_number = self.utils.parse_chapter_number(
                                chapter["href"]
                            ) or self.utils.parse_chapter_number(chapter.text)
                            if str(chapter_number) == start_ch:
                                start_ch_index = i
                                break
                        else:
                            self.logger.warning(
                                "Chapter %s not found. Starting from the beginning.",
                                start_ch,
                            )

                    if end_ch is not None:
                        for i, chapter in enumerate(chapters):
                            chapter_number = self.utils.parse_chapter_number(
                                chapter["href"]
                            ) or self.utils.parse_chapter_number(chapter.text)
                            if str(chapter_number) == end_ch:
                                end_ch_index = (
                                    i + 1
                                )  # +1 to include the end chapter in the slice
                                break
                        else:
                            self.logger.warning(
                                "Chapter %s not found. Downloading up to the last available chapter.",
                                end_ch,
                            )

                    chapters = chapters[start_ch_index:end_ch_index]

                    for chapter in chapters:
                        chapter_number = self.utils.parse_chapter_number(
                            chapter["href"]
                        )
                        chapter_directory = (
                            f"./manga_downloads/{manga_title}/chapter_{chapter_number}"
                        )
                        self.download_files(
                            chapter["href"],
                            chapter_number,
                            chapter_directory,
                            chapter_page_selector,
                            alternative_chapter_page_selector,
                        )
                        if merge_images_into_pdf:
                            self.utils.merge_images_to_pdf(
                                chapter_directory, f"chapter_{chapter_number}"
                            )
                    self.logger.info("All done!")

        except Exception as e:
            self.logger.error(
                "Error getting chapters for %s: %s\n %s",
                manga_title,
                e,
                traceback.format_exc(),
            )
