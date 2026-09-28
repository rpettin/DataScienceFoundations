# Designed by Ryan Pettinger
# Qwen2.5 Coder 1.5b was utilized for autocomplete functionality
# 9/27/26

# Data sets are courtsey of the University of California, San Diego
# Restricted to educational use only.
# https://cseweb.ucsd.edu/~jmcauley/datasets/goodreads.html

import os
import requests
import gzip
import json
import sqlite3

BASE_URL = 'https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/'
TARGET_FILES = {
    'books' : 'goodreads_books.json.gz',
    'authors' : 'goodreads_book_authors.json.gz',
    'genres' : 'goodreads_book_genres_initial.json.gz',
}

class GoodreadsDownloader:
    def __init__(self, content, url, directory=''):
        self.content : str = content
        self.directory : str = directory
        self.URL : str = url
        if not self.Check_Exists():
            self.Pull_From_Web()

    def Get_File_Path(self) -> str: 
        """Return the target file path"""
        return self.directory + self.content + '_json.gz'

    def Get_DB_Path(self) -> str:
        """Return the target database path"""
        return self.directory + 'book_database' + '.db'

    def Check_Exists(self) -> bool:
        """Return if the target data file already exists in the class directory root."""
        if os.path.exists(self.Get_File_Path()):
            print('File already exists in the class directory root.')
            return True
        print('File does not exist in the class directory root.')
        return False

    def Pull_From_Web(self):
        """Download the gz file from the URL, save as {self.content}_json.gz to the class-specified directory"""
        print('Downloading gz file from the URL...')
        response = requests.get(self.URL)
        with open(self.Get_File_Path(), 'wb') as file:
            file.write(response.content)
        print('gz file downloaded successfully.')

    def Print_Lines(self, number_of_lines=100):
        """Print a specified number of lines from gz file in dictionary format. Default is 100 lines."""
        # The files are too large to be opened in normal text editors. So this is used to determine the appropriate SQL schema.
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            for i in range(number_of_lines):
                # Convert line to dictionary format
                data = json.loads(file.readline())
                # pretty print the data
                print(json.dumps(data, indent=4))

    def Print_Targeted_Data(self, target_data, number_of_lines=100):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            for i in range(number_of_lines):
                print(f'Entry #{i+1}')
                data = json.loads(file.readline())
                for target_column in target_data:
                    print(f'    {target_column} : {data.get(target_column, "")}')

    # Opens a SQLite3 DB in the class specified directory
    def OpenDB(self, flush_existing : bool = False):
        '''Opens a SQLite3 DB in the class specified directory'''
        self.db = sqlite3.connect(self.Get_DB_Path())
        self.cursor = self.db.cursor()
        print('DB is open')
        if (flush_existing):
            self.cursor.execute("DROP TABLE books;")
            self.cursor.execute("""CREATE TABLE books (
                database_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goodreads_id INTEGER,
                title_without_series TEXT,
                ratings_count INTEGER,
                average_rating FLOAT,
                publication_year INTEGER,
                number_of_pages INTEGER,
                publisher TEXT,
                author TEXT,
                author_id INTEGER
                genre TEXT
            );""")
            self.db.commit()

    def CloseDB(self):
        '''Closes the SQLite3 DB in the classy'''
        if self.db is not None:
            self.cursor.close()
            self.db.close()
            print('DB is closed')
        print('DB was not open.')

    def Write_SQL(self, processLine : function):
        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        self.OpenDB()
        # Iterate through every line, writing to the sqlite3 database
            
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            counter : float = 0
            EXECUTRE_COUNTER, current_execute_counter = 5000, 0
            
            for line in file:
                counter += 1
                print(f'Processing line: {counter}', end='\r')
                data = json.loads(line)
                            
                processLine(data)
            
                current_execute_counter += 1
                if current_execute_counter >= EXECUTRE_COUNTER:
                    current_execute_counter = 0
                    self.db.commit()
            
            print('Done writing to DB')

        self.CloseDB()


class BookDownloader(GoodreadsDownloader):
    def __init__(self, directory=''):
        self.URL = TARGET_FILES['books']
        self.content = 'books'
        self.TARGET_DATA = [
            'title_without_series',
            'ratings_count',
            'average_rating',
            'publication_year',
            'num_pages',
            'publisher',
            'authors',
            'book_id',
        ]
        self.sql_statement = 'INSERT INTO books (title_without_series, ratings_count, average_rating, publication_year, number_of_pages, publisher, author_id, goodreads_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        super().__init__(self.content, self.URL, directory)

    def Print_Targeted_Data(self, number_of_lines):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        super().Print_Targeted_Data(self.TARGET_DATA, number_of_lines)        

    def ProcessLine(self, data : dict):
            # Build the sql data
            entry_data = []
            for key in self.TARGET_DATA:
                cell = data.get(key, "")

                # Don't record authors if multiple exist
                if type(cell) == list:
                    if (len(cell) > 1) or (len(cell) == 0):
                        cell = ""
                    else:
                        cell = cell[0].get('author_id','')

                entry_data.append(cell)

            self.cursor.execute(self.sql_statement, entry_data)

    def Write_SQL(self):
        super().Write_SQL(self.ProcessLine)


class AuthorDownloader(GoodreadsDownloader):
    def __init__(self, directory=''):
        self.URL = TARGET_FILES['authors']
        self.content = 'authors'
        self.TARGET_DATA = [
            'author_id',
            'average_rating',
            'ratings_count'
        ]
        super().__init__(self.content, self.URL, directory)

    def Print_Targeted_Data(self, number_of_lines):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        super().Print_Targeted_Data(self.TARGET_DATA, number_of_lines)       

    def Write_SQL(self):
        # Placeholder
        pass

class GenreDownloader(GoodreadsDownloader):
    def __init__(self, directory=''):
        self.URL = TARGET_FILES['genres']
        self.content = 'genres'
        self.TARGET_DATA = [
            'book_id',
            'genres'
        ]
        super().__init__(self.content, self.URL, directory)

    def Print_Targeted_Data(self, number_of_lines):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        super().Print_Targeted_Data(self.TARGET_DATA, number_of_lines)       

    def Write_SQL(self):
        # Placeholder
        pass


downloaders = [
    BookDownloader(),
    AuthorDownloader(),
    GenreDownloader()
]
for downloader in downloaders:
    downloader.Print_Targeted_Data(5)

downloaders[0].Write_SQL()

# DB Writes need to start with books. Authors and Genre will modify the entries.

