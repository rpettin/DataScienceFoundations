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

    # Return the target file path
    def Get_File_Path(self):
        return self.directory + self.content + '_json.gz'

    # Return if the target json file already exists in the class directory root.
    def Check_Exists(self):
        if os.path.exists(self.Get_File_Path()):
            print('JSON file already exists in the class directory root.')
            return True
        print('JSON file does not exist in the class directory root.')
        return False


    # Download the JSON file from the URL, save as json.gz to the class directory
    def Pull_From_Web(self):
        print('Downloading JSON file from the URL...')
        response = requests.get(self.URL)
        # Files is several gb in size, download in chuncks
        with open(self.Get_File_Path(), 'wb') as file:
            file.write(response.content)
        print('JSON file downloaded successfully.')

    # Print the first line of gz file in dictionary format
    def Print_First_Line(self):
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            for i in range(100):
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

genreDownloader.Print_First_Line()
# 'book_id'
# 'genres' <- this is a dictionary with the genre as the key and an int as the value. Maybe user votes?