import re
from typing import List

from bs4 import BeautifulSoup
from requests_html import HTMLSession
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def _get_session(url: str):
	session = HTMLSession()
	request = session.get(url)
	if request.ok:
		return request
	else:
		return None

def _save_page(page_html: str, name_file: str, path_output: str = "pages/"):
	with open(path_output + name_file + ".html", "w+") as file:
		file.write(page_html)

def _format_phones(numbers: List[str]):
	numbers = list(map(lambda y: ''.join(filter(lambda x: x.isdigit(), y)), numbers)) # type: ignore
	for i in range(len(numbers)):
		if len(numbers) == 7:
			numbers[i] = "8495" + numbers[i]
		elif numbers[i][0] == "7":
			numbers[i] = "8" + numbers[i][1:]
	return numbers

def _parse_phone_by_tag(page: BeautifulSoup):
	phones = page.find_all("a", href=re.compile("tel:"))
	for i in range(len(phones)):
		phones[i] = phones[i]['href'][4:]
	i = 0

	while i < len(phones) - 1:
		if phones[i] in phones[i + 1]:
			phones.pop(i)
		else:
			i+=1
	return phones


def _find_phone_button(page_url: str):
	#options = webdriver.ChromeOptions()
	#options.add_argument('--headless')
	#driver = webdriver.Chrome(options=options)
	driver = webdriver.Firefox()
	driver.get(page_url)
	try:
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "button")))
	except TimeoutException:
		pass
	phone_buttons = driver.find_elements(By.XPATH, "//button[contains(concat(' ', normalize-space(@class), ' '), 'phone')]")
	number_buttons = driver.find_elements(By.XPATH, "//button[contains(concat(' ', normalize-space(@class), ' '), 'number')]")
	for button in phone_buttons:
		button.click()
	for button in number_buttons:
		if button not in phone_buttons:
			button.click()
	page = driver.page_source
	driver.quit()
	return page


def phone_parser(urls: List[str]):
	all_phones = []
	for page_url in urls:

		if not (page := _get_session(page_url)):
			print(f"Can't open page. URL: {page_url}")
			continue

		parser_page = BeautifulSoup(page.html.html, 'html.parser')

		#parse phone from page by tag
		if site_phones := _parse_phone_by_tag(parser_page):
			_save_page(page.html.html, parser_page.title.contents[0])
			all_phones += site_phones
			continue

		#find button to open number
		if not site_phones:
			update_page = _find_phone_button(page_url)
			parser_page = BeautifulSoup(update_page, 'html.parser')
			_save_page(update_page, parser_page.title.contents[0])
			if site_phones := _parse_phone_by_tag(parser_page):
				all_phones += site_phones
				continue
	# formut numbers
	all_phones = _format_phones(all_phones)
	return all_phones


if __name__=="__main__":
	print(phone_parser([
		"https://repetitors.info",
		"https://hands.ru/company/about"
	]))
