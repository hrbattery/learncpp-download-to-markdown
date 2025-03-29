# LearnCPP Downloader to Markdown

Multi-threaded web scraper to download all the tutorials from <a href="https://www.learncpp.com/">www.learncpp.com</a> and convert them to Markdown files concurrently.

This project is base on [amalrajan's work](https://github.com/amalrajan/learncpp-download). My purpose is to translate the tutorial and using in webpage, therefore I convert them into Markdown format instead of PDF.

## Usage

### Local

You need Python 3.13+ installed on your system, or adjust the dependencies - It's no a complex program :) 

#### Run it

Clone the repository

```bash
git clone https://github.com/hrbattery/learncpp-download-to-markdown.git
```

Install Python dependencies

```bash
cd learncpp-download-to-markdown
pip install -r requirements.txt
```

Run the script

```bash
scrapy crawl learncpp 
```

You'll find the downloaded files inside `learncpp/md` directory under the repository root directory.

## FAQ

**Rate Limit Errors:**

- Modify `settings.py`.
- Increase `DOWNLOAD_DELAY` (default: 0) to 0.2.

**High CPU Usage:**

- Adjust `max_workers` in `learncpp.py`.
- Decrease from default 192 to reduce CPU load.

```python
self.executor = ThreadPoolExecutor(
    max_workers=192
)  # Limit to 192 concurrent PDF conversions
```

## License

[GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.en.html)
