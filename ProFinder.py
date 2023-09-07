import requests
import pandas as pd
from bs4 import BeautifulSoup


class LeaguepediaScraper:
    """Class to scrape data from Leaguepedia website regarding professional LOL players"""

    def __init__(self):
        self.url_template = "https://lol.fandom.com/wiki/{page}"

    def __get_page(self, page) -> BeautifulSoup:
        """Gets the HTML of the page"""
        url = self.url_template.format(page=page)
        response = requests.get(url)
        return BeautifulSoup(response.text, 'html.parser')

    def __special_search(self, search_term: str) -> BeautifulSoup:
        """Searches for a player using the query in the search bar and returns the soup object of the page"""
        url = self.url_template.format(
            page=f"Special:Search?query={search_term}")
        response = requests.get(url)
        return BeautifulSoup(response.text, 'html.parser')

    def __search_pro_page(self, summoner_name: str, given_name: str, family_name: str) -> BeautifulSoup:
        """Finds the page of the professional player, given their summoner name, and full name 
        returns the soup object"""
        # First try the summoner name
        soup = self.__get_page(summoner_name)
        page_type = self.__check_page(soup)

        if page_type == "disambiguation":
            page = self.__find_disambiguation(
                soup, summoner_name, given_name, family_name)
            soup = self.__get_page(page)

        elif page_type == "doesn't exist":
            search_soup = self.__special_search(summoner_name)
            # Use the find_disambiguation function to find the correct link
            page = self.__find_disambiguation(
                search_soup, summoner_name, given_name, family_name)
            soup = self.__get_page(page)

        page_type = self.__check_page(soup)
        if page_type == "article":
            return soup
        
        # If not found, print "Not Found"
        print("Not Found")
        return None

    def __find_disambiguation(self, soup: BeautifulSoup, summoner_name: str, first_name: str, family_name: str) -> str:
        """Given a soup object containing a disambiguation page, find the correct link

        Args:
            soup (BeautifulSoup): the soup object for the disambiguation page
            first_name (str): the player's first name
            family_name (str): the player's family name
        """
        for link in soup.find_all("a"):
            if first_name in link.text or family_name in link.text:
                # Return the href
                return link.get("href")[6:]
        else:
            raise Exception("Summoner Not Found")

    def __check_page(self, soup):
        # Check if the page is an article, a disambiguation page, or a "doesn't exist" page

        # If it's an article, return "article"
        article_text = "Soloqueue IDs"

        # If it's a disambiguation page, return "disambiguation"
        disambiguation_text = "This disambiguation page lists articles associated with the same title."

        # If it's a "doesn't exist" page, return "doesn't exist"
        doesnt_exist_text = "There is currently no text in this page."

        if doesnt_exist_text in soup.text:
            return "doesn't exist"
        elif disambiguation_text in soup.text:
            return "disambiguation"
        elif article_text in soup.text:
            return "article"

        # If it's something else, return "other"
        return "other"

    def __parse_pro_soloq_ids(self, soup: BeautifulSoup) -> dict:
        # Go through the tables and look for <td class="infobox-label">Soloqueue IDs</td>
        tables = soup.find_all("table", class_="infobox")

        for table in tables:
            for row in table.find_all("tr"):
                # If row.text starts with "Soloqueue IDs", save the row
                search_string = "Soloqueue IDs"
                if row.text.startswith("Soloqueue IDs"):
                    break

        # Get the contents inside all the <b> tag in the rows
        server = row.find_all("b")
        # Iterate through all the server names, and get the text following them in the row variable
        ids = {}
        # Zip the two lists together into a dictionary
        for s in server:
            ids[s.text] = s.next_sibling.strip().split(", ")
        return ids

    def get_pro_soloq_ids(self, summoner_name: str, first_name: str, family_name: str) -> dict:
        """Finds the pro player's soloq ids and return it 
        as a dictionary containing the region as keys and the ids as a list of strings

        Args:
            summoner_name (str): the pro player's summoner name
            first_name (str): the pro player's first/given name
            family_name (str): the pro player's family name

        Returns:
            dict: A dictionary of the pro player's soloq ids with the region as keys and the ids as a list of strings
        """
        soup = self.__search_pro_page(summoner_name, first_name, family_name)
        ids = self.__parse_pro_soloq_ids(soup)
        return ids


if __name__ == "__main__":
    scraper = LeaguepediaScraper()
    ids = scraper.get_pro_soloq_ids("Nobody", "Nicolas", "Ale")
    print(ids)
