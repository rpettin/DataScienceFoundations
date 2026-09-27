# Designed by Ryan Pettinger
# Qwen2.5 Coder 1.5B was utilized for autocomplete functionality
# 9/27/26

import os
import requests
import gzip
import json

BASE_URL = 'https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/'
TARGET_FILES = {
    'books' : 'goodreads_books.json.gz',
    'authors' : 'goodreads_book_authors.json.gz',
    'genres' : 'goodreads_book_genres_initial.json.gz',
}

class BookDownloader:
    def __init__(self, content, url, directory=''):
        self.content : str = content
        self.directory : str = directory
        self.URL : str = url
        print(self.Get_File_Path())
        if not self.Check_Exists():
            self.Pull_From_Web()

    def Get_File_Path(self) -> str: 
        """Return the target file path"""
        return self.directory + self.content + '_json.gz'

    def Check_Exists(self) -> bool:
        """Return if the target data file already exists in the class directory root."""
        if os.path.exists(self.Get_File_Path()):
            print('File already exists in the class directory root.')
            return True
        print('File does not exist in the class directory root.')
        return False

    def Pull_From_Web(self):
        """Download the gz file from the URL, save as {self.content}_json.gz to the class-specified directory"""
        print('Downloading JSON file from the URL...')
        response = requests.get(self.URL)
        with open(self.Get_File_Path(), 'wb') as file:
            file.write(response.content)
        print('JSON file downloaded successfully.')


    def Print_Lines(self, number_of_lines=100):
        """Print a specified number of lines from gz file in dictionary format. Default is 100 lines."""
        # The files are too large to be open in normal text editors. So this is used to determine the appropriate SQL schema.
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            for i in range(number_of_lines):
                # Convert line to dictionary format
                data = json.loads(file.readline())
                # pretty print the data
                print(json.dumps(data, indent=4))


bookDownloader = BookDownloader('books', BASE_URL + TARGET_FILES['books']) 
# 'title_without_series'
# 'ratings_count'
# 'average_rating'
# 'publication_year'
# 'num_pages'
# 'publisher'
# 'authors' <- LIST!!!
#       'author_id' <- reference
# 'book_id'
authorDownloader = BookDownloader('authors', BASE_URL + TARGET_FILES['authors']) 
# 'author_id'
# 'average_rating'
# 'ratings_count'
genreDownloader = BookDownloader('genres', BASE_URL + TARGET_FILES['genres']) # References book id, contains multiple generes
# 'book_id'
# 'genres' <- this is a dictionary with the genre as the key and an int as the value. Maybe user votes?

genreDownloader.Print_Lines()