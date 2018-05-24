import argparse
import os
import platform
import sys
import urllib.request

import bs4 as bs
import pdfkit


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        type=str, help="download location")
    parser.add_argument('--nopdf', action='store_true',
                        default=False, help="skip converting to pdf")
    # parser.add_argument('--combine')
    # Next release will include a combine feature.

    args = parser.parse_args()

    if args.output[-1] not in ('/', '\''):
        if user_os == 'Windows':
            args.output += '\''
        elif user_os == 'Linux':
            args.output += '/'

    sys.stdout.write(str(main(args)))


def get_urls():
    # Scrapes the URLs off the website.
    global urls

    sauce = urllib.request.urlopen("http://www.learncpp.com").read()
    soup = bs.BeautifulSoup(sauce, 'lxml')

    urls = ()

    for i in soup.find_all('a'):
        url = i.get('href')
        if url and 'cpp-tutorial' in url:
            if 'http://' not in url:
                url = "http://www.learncpp.com" + url
            urls += (url,)

    return urls


def save_as_pdf(url, dest):
    # For saving the web page in PDF format.

    title = dest + delimiter + url.split('/')[-2].replace(' ', '_') + '.pdf'
    pdfkit.from_url(url, title)


def save_as_html(url, dest):
    # For saving web pages to the permanent storage media.
    data = urllib.request.urlopen(url).read()
    title = url.split('/')[-2].replace(' ', '_') + '.html'
    with open("{}\{}".format(dest, title), 'wb') as f:
        f.write(data)


def main(args):
    # Main function.
    urls = get_urls()
    length = len(urls)

    for i, url in enumerate(urls):
        print("Downloading {} of {} ...".format(i + 1, length))

        if args.nopdf:
            try:
                save_as_html(url, dest=args.output)
            except KeyboardInterrupt:
                print("Process terminated by the user.")
                sys.exit()
            except Exception as e:
                print("Process failed.")
                print(e)
                sys.exit(1)

        else:

            if sys.platform == 'win32':
                if os.path.exists(
                        "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"):
                    path_wkthmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
                else:
                    path_wkthmltopdf = "C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
                # config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
                # ^ to be configured for Windows

            # Else, manually specify a custom path.

            try:
                save_as_pdf(url, args.output)
            except KeyboardInterrupt:
                print("Process terminated by the user.")
                sys.exit()
            except Exception as e:
                print(e)
                pass


if __name__ == '__main__':
    urls = None
    user_os = platform.system()

    if user_os == 'Windows':
        delimiter = '\\'
    else:
        delimiter = '//'

    argument_parser()
