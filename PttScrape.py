import requests
from bs4 import BeautifulSoup
import time
import random


# Turn on text_mode to parse the local files(text_mode_article_list & text_mode_article) for the test.
# Turn off text_mode to get the scrape_website html data, and overwrite it to the local files.
# Using scrape_keywords to find the text with 'M'andatory or 'O'ptional keywords.
# It will save the scraped result into scrape_result_file with article title, link, keywords, and content.
# The program will continually get the last page until the counter is meeting to scrape_max_page.
# There is a 5-10 sec delay between articles, and 20 sec delay between pages.

text_mode = False
text_mode_article_list = 'Article_List.html'
text_mode_article = 'Article.html'

scrape_website = 'https://www.ptt.cc/bbs/Soft_Job/'
scrape_keywords = {'M': ['python'],
                   'O': ['machine learning', 'tensorflow']}
scrape_result_file = 'ScrapeResult.txt'
scrape_max_page = 1


def read_file(filename, op):
    with open(filename, op) as fin:
        return fin.read()


def write_file(filename, text, op):
    if not text_mode:
        with open(filename, op) as fout:
            fout.write(text)


def scrape_with_keyword(is_mandatory, keyword, soup, kw_found):
    content = set()
    article_content = [element for element in soup.find('div', class_='bbs-screen bbs-content')
                       if str(element.string).lower().find(keyword) != -1]
    push_content = [element for element in soup.findAll('span', class_='push-content')
                    if element.name and str(element.text).lower().find(keyword) != -1]

    if is_mandatory and not article_content and not push_content: return set()
    content |= {str(text.string) for text in article_content if text.string}
    content |= {str(text.string) for text in push_content if text.string}
    if content: kw_found.append(keyword)
    return content


def scrape_article(html_text, kw_found):
    soup = BeautifulSoup(html_text, 'lxml')
    write_file(text_mode_article, soup.prettify(), 'wt')
    content = set()
    for keyword in scrape_keywords['M']:
        content |= scrape_with_keyword(True, keyword.lower(), soup, kw_found)
    for keyword in scrape_keywords['O']:
        content |= scrape_with_keyword(False, keyword.lower(), soup, kw_found)

    return list(content)


def scrape_article_list(html_text):
    soup = BeautifulSoup(html_text, 'lxml')
    write_file(text_mode_article_list, soup.prettify(), 'wt')
    links = [element for element in soup.find_all('div', class_='title') if element.a]

    for link in links:
        lines, kw_found = [], []
        if not text_mode:
            next_website = scrape_website + ''.join(link.a.get('href').split('/')[3:])  # TODO: General for all website.
            print('\n', next_website)
            r = requests.get(next_website)
            time.sleep(random.randint(5, 10))
            if r.status_code == requests.codes.ok:
                lines = scrape_article(r.text, kw_found)
            else:
                print('\n[scrape_article_list]', 'Request fail:', r.status_code)
        else:
            lines = scrape_article(read_file(text_mode_article, 'rt'), kw_found)

        if not lines: continue
        print('Title: ' + link.a.text.strip())
        write_file(scrape_result_file, '\n\nTitle: ' + link.a.text.strip() + '\n', 'at')
        print('Link : ' + link.a.get('href'))
        write_file(scrape_result_file, 'Link : ' + link.a.get('href') + '\n', 'at')
        print('Keywords found: ' + ','.join(kw_found))
        write_file(scrape_result_file, 'Keywords found: ' + ','.join(kw_found) + '\n', 'at')
        for line in lines:
            print(line)
            write_file(scrape_result_file, line + '\n', 'at')

    last_page = [element.get('href') for element in soup.findAll('a', class_='btn wide')
                 if str(element.string).find('上頁') != -1]
    return last_page[0].split('/')[-1] if last_page else ''


print('Text Mode:', 'ON' if text_mode else 'OFF')
write_file(scrape_result_file, 'Text Mode: ON\n\n' if text_mode else 'Text Mode: OFF\n\n', 'wt')
if not text_mode:
    index = ''
    for page in range(scrape_max_page):
        r = requests.get(scrape_website + index)
        if r.status_code == requests.codes.ok:
            index = scrape_article_list(r.text)
            if index == '': break
            print('\nNext Page:', scrape_website + index)
        else:
            print('\n[main]', 'Request fail:', r.status_code)
        time.sleep(20)
else:
    scrape_article_list(read_file(text_mode_article_list, 'rt'))
