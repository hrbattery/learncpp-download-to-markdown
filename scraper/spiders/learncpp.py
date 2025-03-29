import dataclasses
import logging
import os
import pathlib
import typing
import urllib.request
from concurrent.futures import ThreadPoolExecutor
# from markdownify import markdownify as convert_to_markdown
from markdown_converter import convert_to_markdown
from pathvalidate import sanitize_filename
import mdformat

import bs4
import pdfkit
import scrapy


@dataclasses.dataclass
class URL:
    url: str
    chapter_dirname: str
    url_index: str


class LearncppSpider(scrapy.Spider):
    name = "learncpp"
    allowed_domains = ["learncpp.com"]

    # Define ThreadPoolExecutor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(
            max_workers=192
        )  # Limit to 192 concurrent PDF conversions

    def create_working_directory(self) -> None:
        # Create a directory named "learncpp" if it doesn't exist
        if not os.path.exists(self.name):
            os.mkdir(self.name)
        self.log(f"Created working directory: {self.name}")

    def start_requests(self) -> typing.Union[scrapy.Request, None]:
        # Create a working directory
        self.create_working_directory()

        # Use get_urls function to dynamically generate start_urls
        urls = self.get_urls()
        self.log(f"Found {len(urls)} URLs to scrape.")

        for url in urls:
            self.log(f"Processing URL: {url.url}")

            # Yield a Request object for each URL
            yield scrapy.Request(
                url=url.url,
                callback=self.parse,
                cb_kwargs={
                    "page_index": url.url_index,
                    "chapter_dirname": url.chapter_dirname
                },
            )

    def parse(
        self,
        response: scrapy.http.response.Response,
        page_index: str,
        chapter_dirname: str
    ) -> None:
        # Modify the filename to include the index
        parsed_url = pathlib.Path(response.url)
        filename = f"{page_index}-{parsed_url.parts[-1]}.html"
        self.log(f"Processing HTML for {filename}")

        _dirname = pathlib.Path(self.name, "html", chapter_dirname)
        # Save the HTML file
        if not _dirname.exists():
            _dirname.mkdir(parents=True, exist_ok=True)
        self.log(f"Created working directory: {_dirname}")

        with open(_dirname.joinpath(filename), "wb") as f:
            f.write(response.body)
        self.log(f"Saved HTML file: {_dirname.joinpath(filename)}")

        # Clean the HTML file
        self.clean(_dirname.joinpath(filename))
        self.log(f"Cleaned HTML for {_dirname.joinpath(filename)}")

        # Convert html file
        with open(_dirname.joinpath(filename), "r") as f:
            html_content = f.read()

            # Run convert_to_markdown function in a ThreadPool
            self.executor.submit(self.convert_to_markdown, html_content, chapter_dirname, filename)
            self.log(f"Started PDF conversion for {filename}")

    def clean(self, filename: pathlib.Path) -> None:
        # Read the HTML file
        with open(str(filename), "r", encoding="utf-8") as file:
            html_content = file.read()

        # Parse the HTML content
        soup = bs4.BeautifulSoup(html_content, "html.parser")

        # List of div IDs to remove
        div_ids_to_remove = [
            "comments",
            "site-header-main",
            "header-image-main",
            "colophon-inside",
        ]

        # Class name to remove
        classes_to_remove = ["code-block code-block-10", "cf_monitor"]

        # Remove elements by tag, attribute, and values
        self.remove_elements_by_attribute(
            soup,
            "div",
            "id",
            div_ids_to_remove,
        )
        self.remove_elements_by_attribute(
            soup,
            "div",
            "class",
            classes_to_remove,
        )

        # Remove the footer
        self.remove_elements_by_attribute(
            soup, "footer", "class", ["entry-meta entry-utility"]
        )

        # Save the modified HTML content
        with open(str(filename), "w", encoding="utf-8") as file:
            file.write(str(soup))
        self.log(f"Saved cleaned HTML for {str(filename)}")

    def remove_elements_by_attribute(
        self,
        soup: bs4.BeautifulSoup,
        tag: str,
        attribute: str,
        values: typing.List[str],
    ) -> None:
        for value in values:
            elements = soup.find_all(tag, {attribute: value})
            for element in elements:
                element.decompose()

    def convert_to_markdown(self, content: str, chapter_dirname: str, filename: str) -> None:
        markdown_filename = pathlib.Path(filename).with_suffix(".md")
        md_dirname = pathlib.Path(self.name, "md", chapter_dirname)
        
        if not md_dirname.exists():
            md_dirname.mkdir(parents=True, exist_ok=True)
        self.log(f"Created working directory: {md_dirname}")

        try:
            md_content = convert_to_markdown(
                content,
                autolinks=True,
                code_language="cpp",
                heading_style="atx"
            )
            formatted_md_content = mdformat.text(md_content)
            with open(md_dirname.joinpath(markdown_filename), "w", encoding='utf-8') as file:
                file.write(formatted_md_content)
        except OSError as e:
            self.log(f"write file error: {e}", logging.ERROR)

        self.log(f"Converted {filename} to PDF: {markdown_filename}")
            
    def convert_to_pdf(self, filename: str) -> None:
        # Original file path
        pdf_filename = pathlib.Path(filename).with_suffix(".pdf")

        # Convert the modified HTML file to PDF
        try:
            pdfkit.from_file(
                os.path.join(self.name, filename),
                os.path.join(self.name, pdf_filename),
                options={"enable-local-file-access": ""},
            )
        except OSError as e:
            if (
                "QNetworkReplyImplPrivate::error: Internal problem, this method must only be called once."
                in str(e)
            ):
                # If so, suppress the error
                pass
            else:
                self.log(f"Convert pdf failed: {e}", logging.ERROR)

        self.log(f"Converted {filename} to PDF: {pdf_filename}")

    def get_urls(self) -> typing.List[URL]:
        try:
            # Parse the HTML content with BeautifulSoup
            html_content = urllib.request.urlopen(
                urllib.request.Request(
                    "http://www.learncpp.com",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
            ).read()
        except urllib.error.URLError as e:
            self.log(f"Error accessing the website: {e}", logging.ERROR)
            return []

        try:
            soup = bs4.BeautifulSoup(html_content, "html.parser")

            # Find all divs with class "lessontable" first, to get header first
            all_chapter_tables = soup.find_all("div", class_="lessontable")

            # List to store the URLs
            fetched_urls = []
            
            for chapter in all_chapter_tables:
                # Calculate chapter folder name
                header: str = chapter.find_next("div", class_="lessontable-header")
                
                chapter_index = header.find_next("a")["name"].replace("Chapter", "")
                chapter_name = header.find_next("div", class_="lessontable-header-title").text

                chapter_dirname = sanitize_filename(f"{chapter_index}-{chapter_name}")

                # Iterate each lesson chapter now
                page_index = 1

                # Find all divs with class "lessontable-row-title"
                all_lesson_divs = chapter.find_all("div", class_="lessontable-row-title")

                for div in all_lesson_divs:
                    all_a_tags = div.find_all("a")

                    # Iterate through each div and find all <a> tags inside
                    for a_tag in all_a_tags:
                        # Append the URL to the list
                        parsed_url = URL(
                            a_tag["href"],
                            chapter_dirname,
                            f"{chapter_index}-{page_index}"
                        )
                        fetched_urls.append(parsed_url)

                        # Increment the index
                        page_index += 1

            self.log(f"Successfully fetched {len(fetched_urls)} URLs")
            return fetched_urls

        except Exception as e:
            self.log(f"Error parsing HTML content: {e}",logging.ERROR)
            return []
