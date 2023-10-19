import re
from typing import List

from bs4 import BeautifulSoup
from requests import Response
from requests_html import HTMLSession
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class PhoneParser():

	def _get_session(self, url: str) -> Response | None:
		"""Setting a session using a URL. If the session has successfully started returns :class:`Response` object else returns :class:`NoneType`.

		:param url: URL for the new :class:`Request` object,
		:rtype: request.Response | None
		"""


		session = HTMLSession()
		request = session.get(url)
		if request.ok:
			return request
		else:
			return None

	def _save_page(self, page_html: str, name_file_output: str, path_output: str = "pages/") -> None:
		"""Saves HTML to the specified address in the specified file

		:param page_html: HTML that should be saved,
		:param name_file: Name of the file to be saved,
		:param path_output: Path to file to be saved,
		:rtype: NoneType
		"""


		with open(path_output + name_file_output + ".html", "w+") as file:
			file.write(page_html)

	def _format_phones(self, numbers: list[str]) -> list[str]:
		"""This method format all numbers to the form '8xxxnnnnnn'.

		:param number: List of all number, that should be format,
		:rtype: list[str]
		"""


		numbers = list(map(lambda y: ''.join(filter(lambda x: x.isdigit(), y)), numbers)) # type: ignore

		for i in range(len(numbers)):
			if len(numbers) == 7:
				numbers[i] = "8495" + numbers[i]
			elif numbers[i][0] == "7":
				numbers[i] = "8" + numbers[i][1:]
		return numbers

	def _parse_phone_by_tag(self, page: BeautifulSoup) -> list[str]:
		"""This method find all tags <a>, that have 'tel:' in argument 'href'.
		:param page: BeautifulSoup object that can be use for parse,
		:rtype: list[str]
		"""


		phones_result = page.find_all("a", href=re.compile("tel:"))
		phones = list()

		for i in range(len(phones_result)):
			phones.append(phones_result[i]['href'][4:])
		i = 0

		while i < len(phones) - 1:
			if phones[i] in phones[i + 1]:
				phones.pop(i)
			else:
				i+=1

		return phones

	def _click_phone_buttons(self, page_url: str) -> str:
		"""This method find all button that have word 'phone' or 'number' and clicked by them.
		:param page: HTML of current page,
		:rtype: HTML of updated page
		"""


		# Run using Google Chrome
		# options = webdriver.ChromeOptions()
		# options.add_argument('--headless')
		# driver = webdriver.Chrome(options=options)

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

	def phone_parser(self, urls: List[str]) -> list[str]:
		"""Find all numbers from pages. Returns list of numbers in format '8xxxnnnnnn'.
		:param urls: List of pages URL,
		:rtype: list[str]
		"""


		all_phones = []
		for page_url in urls:

			if not (page := self._get_session(page_url)):
				print(f"Can't open page. URL: {page_url}")
				continue

			parser_page = BeautifulSoup(page.html.html, 'html.parser') # type: ignore
			#parse phone from page by tag
			if site_phones := self._parse_phone_by_tag(parser_page):
				self._save_page(page.html.html, parser_page.title.contents[0].text) # type: ignore
				all_phones += site_phones
				continue

			#find button to open number
			if not site_phones:
				update_page = self._click_phone_buttons(page_url)
				parser_page = BeautifulSoup(update_page, 'html.parser')
				self._save_page(update_page, parser_page.title.contents[0].text) # type: ignore
				if site_phones := self._parse_phone_by_tag(parser_page):
					all_phones += site_phones
					continue

		# format numbers
		all_phones = self._format_phones(all_phones)

		return all_phones


if __name__ == "__main__":
	print(
		PhoneParser().phone_parser([
			"https://repetitors.info",
			"https://hands.ru/company/about"
		])
	)
