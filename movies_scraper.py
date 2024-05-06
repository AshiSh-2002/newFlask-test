# import requests
# from bs4 import BeautifulSoup


# url_list = {}
# api_key = "e91bb57fcabd6f4d0eaed92716cf5a5356ea54e2"
 

# def search_movies(query):
#     movies_list = []
#     movies_details = {}
#     website = BeautifulSoup(requests.get(f"https://mkvcinemas.skin/?s={query.replace(' ', '+')}").text, "html.parser")
#     movies = website.find_all("a", {'class': 'ml-mask jt'})
#     for movie in movies:
#         if movie:
#             movies_details["id"] = f"link{movies.index(movie)}"
#             movies_details["title"] = movie.find("span", {'class': 'mli-info'}).text
#             url_list[movies_details["id"]] = movie['href']
#         movies_list.append(movies_details)
#         movies_details = {}
#     return movies_list


# def get_movie(query):
#     movie_details = {}
#     movie_page_link = BeautifulSoup(requests.get(f"{url_list[query]}").text, "html.parser")
#     if movie_page_link:
#         title = movie_page_link.find("div", {'class': 'mvic-desc'}).h3.text
#         movie_details["title"] = title
#         img = movie_page_link.find("div", {'class': 'mvic-thumb'})['data-bg']
#         movie_details["img"] = img
#         links = movie_page_link.find_all("a", {'rel': 'noopener', 'data-wpel-link': 'internal'})
#         final_links = {}
#         for i in links:
#             url = f"https://urlshortx.com/api?api={api_key}&url={i['href']}"
#             response = requests.get(url)
#             link = response.json()
#             final_links[f"{i.text}"] = link['shortenedUrl']
#         movie_details["links"] = final_links
#     return movie_details


import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import os

# Define an API key from environment variables for security
api_key = "e91bb57fcabd6f4d0eaed92716cf5a5356ea54e2"

def search_movies(query):
    """
    Searches for movies based on the query and returns a list of movies with basic information.
    """
    movies_list = []
    try:
        # Get the website content
        response = requests.get(f"https://mkvcinemas.skin/?s={query.replace(' ', '+')}")
        response.raise_for_status()  # Raise exception for HTTP errors
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all movie links
        movie_links = soup.find_all("a", {'class': 'ml-mask jt'})
        
        # Populate the movies_list
        for index, movie in enumerate(movie_links):
            title_element = movie.find("span", {'class': 'mli-info'})
            if title_element:
                movie_info = {
                    "id": f"link{index}",
                    "title": title_element.text,
                    "url": movie['href']
                }
                movies_list.append(movie_info)
    except RequestException as e:
        print("Error fetching movies:", e)
    
    return movies_list


def get_movie(movie_id, movie_url):
    """
    Retrieves detailed information about a specific movie, including download links.
    """
    movie_details = {}
    try:
        response = requests.get(movie_url)
        response.raise_for_status()  # Raise exception for HTTP errors
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get movie title and image
        title_div = soup.find("div", {'class': 'mvic-desc'})
        img_div = soup.find("div", {'class': 'mvic-thumb'})
        
        if title_div and img_div:
            movie_details["title"] = title_div.h3.text
            movie_details["img"] = img_div['data-bg']

            # Get download links and shorten them
            link_elements = soup.find_all("a", {'rel': 'noopener', 'data-wpel-link': 'internal'})
            final_links = {}
            
            for link in link_elements:
                shortened_url = shorten_url(link['href'])
                if shortened_url:  # Check if shortening succeeded
                    final_links[f"{link.text}"] = shortened_url
            
            movie_details["links"] = final_links
    
    except RequestException as e:
        print("Error fetching movie details:", e)
    
    return movie_details


def shorten_url(original_url):
    """
    Shortens a given URL using the provided API key.
    """
    shortened_url = None
    try:
        url = f"https://urlshortx.com/api?api={api_key}&url={original_url}"
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        shortened_response = response.json()
        shortened_url = shortened_response.get("shortenedUrl", original_url)
    except RequestException as e:
        print("Error shortening URL:", e)
    
    return shortened_url
