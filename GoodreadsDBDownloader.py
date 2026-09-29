# Designed by Ryan Pettinger
# Qwen2.5 Coder 1.5b was utilized for autocomplete functionality
# 9/29/26

# Data sets are courtesy of the University of California, San Diego
# Restricted to educational use only.
# https://cseweb.ucsd.edu/~jmcauley/datasets/goodreads.html

import os
import requests
import gzip
import json
import sqlite3
import time

TARGET_FILES = {
    'books' : 'goodreads_books.json.gz',
    'authors' : 'goodreads_book_authors.json.gz',
    'genres' : 'goodreads_book_genres_initial.json.gz',
}

class GoodreadsDownloader:
    def __init__(self, content, url, directory=''):
        self.BASE_URL = 'https://mcauleylab.ucsd.edu/public_datasets/gdrive/goodreads/'

        self.content : str = content
        self.directory : str = directory
        self.URL : str = self.BASE_URL + url
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
        # Requests code referenced from https://github.com/MengtingWan/goodreads/blob/master/download.ipynb
        response = requests.get(self.URL, timeout=60)
        # Referenced from class material
        response.raise_for_status()
        with open(self.Get_File_Path(), 'wb') as file:
            file.write(response.content)
        print('gz file downloaded successfully.')

    def Print_Lines(self, number_of_lines=100):
        """Print a specified number of lines from gz file in dictionary format. Default is 100 lines."""
        # The files are too large to be opened in normal text editors. So this is used to determine the appropriate SQL schema.
        # gzip code referenced from https://gist.github.com/0ut0fcontrol/baac52eb7119d6455883451b711d3478
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            for i in range(number_of_lines):
                # Convert line to dictionary format
                data = json.loads(file.readline())
                # pretty print the data
                print(json.dumps(data, indent=4))

    def Print_Targeted_Data(self, target_data, number_of_lines=100):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        # gzip code referenced from https://gist.github.com/0ut0fcontrol/baac52eb7119d6455883451b711d3478
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            for i in range(number_of_lines):
                print(f'Entry #{i+1}')
                data = json.loads(file.readline())
                for target_column in target_data:
                    print(f'    {target_column} : {data.get(target_column, "")}')

    def Open_DB(self, flush_existing : bool = False):
        '''Opens a SQLite3 DB in the class specified directory'''
        self.db = sqlite3.connect(self.Get_DB_Path())
        self.cursor = self.db.cursor()
        print('DB is open')
        if (flush_existing):
            self.cursor.execute("DROP TABLE IF EXISTS books;")
            self.cursor.execute("""CREATE TABLE books (
                database_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goodreads_id INTEGER,
                country_code TEXT,
                language_code TEXT,
                genre TEXT,
                fiction_or_non TEXT,
                title_without_series TEXT,
                ratings_count INTEGER,
                average_rating FLOAT,
                publication_year INTEGER,
                number_of_pages INTEGER,
                publisher TEXT,
                author TEXT,
                author_id INTEGER
            );""")
            self.db.commit()

    def Close_DB(self):
        '''Closes the SQLite3 DB in the class'''
        if self.db is not None:
            self.cursor.close()
            self.db.close()
            print('DB is closed')
        else:
            print('DB was not open.')

    def Write_SQL(self, processLine, commit_after : int = 5000, flush_existing : bool = False):
        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        self.Open_DB(flush_existing)
        # Iterate through every line, writing to the sqlite3 database
            
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            counter : int = 0
            current_execute_counter = 0
            
            for line in file:
                counter += 1
                print(f'Processing line: {counter}', end='\r')
                data = json.loads(line)
                            
                processLine(data)
            
                current_execute_counter += 1
                if current_execute_counter >= commit_after:
                    current_execute_counter = 0
                    self.db.commit()

            # Final commit if last batch is less than 5k
            self.db.commit()
            print('\nDone writing to DB')

        self.Close_DB()


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
            'language_code',
            'country_code'
        ]
        self.sql_statement = 'INSERT INTO books (title_without_series, ratings_count, average_rating, publication_year, number_of_pages, publisher, author_id, goodreads_id, language_code, country_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        super().__init__(self.content, self.URL, directory)

    def Print_Targeted_Data(self, number_of_lines):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        super().Print_Targeted_Data(self.TARGET_DATA, number_of_lines)        

    def Process_Line(self, data : dict):
            '''Uniquely processes the data and writes it to the SQL database. Passed as an argument into the parent's write sql function'''
            entry_data = []
            for key in self.TARGET_DATA:
                cell = data.get(key, "")

                if type(cell) == list:
                    if (len(cell) == 0):
                        cell = "" # No recorded author
                    elif (len(cell) > 1):
                        cell = "-1" # This will represent multiple authors
                    else:
                        cell = cell[0].get('author_id','')

                entry_data.append(cell)

            self.cursor.execute(self.sql_statement, entry_data)

    def Write_SQL(self):
        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        super().Write_SQL(self.Process_Line, flush_existing=True) # Drops the existing database before adding the new entries


class AuthorDownloader(GoodreadsDownloader):
    def __init__(self, directory=''):
        self.URL = TARGET_FILES['authors']
        self.content = 'authors'
        self.TARGET_DATA = [
            'name',
            'author_id',
        ]
        # Updates the SQL author name where the author id matches the existing id
        self.sql_statement = 'UPDATE books SET author = ? WHERE author_id = ?'
        super().__init__(self.content, self.URL, directory)

    def Print_Targeted_Data(self, number_of_lines):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        super().Print_Targeted_Data(self.TARGET_DATA, number_of_lines)       

    def Process_Line(self, data : dict):
        '''Uniquely processes the data and writes it to the SQL database. Passed as an argument into the super's write sql function'''
        entry_data = []
        for key in self.TARGET_DATA:
            cell = data.get(key, "")
            entry_data.append(cell)
        self.cursor.execute(self.sql_statement, entry_data)

    def Write_SQL(self):
        # The author id column needs to be indexed or else this is extremely slow
        self.Open_DB()
        print('Indexing author_id...')
        sql_statement = 'CREATE INDEX IF NOT EXISTS idx_books_author_id ON books(author_id);'
        self.cursor.execute(sql_statement)
        self.db.commit()
        self.Close_DB()

        super().Write_SQL(self.Process_Line)

        # The author_id index is no longer needed.
        self.Open_DB()
        print('Removing author_id index...')
        sql_statement = 'DROP INDEX IF EXISTS idx_books_author_id;'
        self.cursor.execute(sql_statement)
        self.db.commit()
        self.Close_DB()

class GenreDownloader(GoodreadsDownloader):
    def __init__(self, directory=''):
        self.URL = TARGET_FILES['genres']
        self.content = 'genres'
        self.TARGET_DATA = [
            'genres',
            'book_id'
        ]
        # SQL statement updates the book genre where the id matches the "goodreads_id" column
        self.sql_statement = 'UPDATE books SET fiction_or_non = ?, genre = ? WHERE goodreads_id = ?'
        super().__init__(self.content, self.URL, directory)

    def Print_Targeted_Data(self, number_of_lines):
        """Extracts the target data from the first 100 lines (default) of the gz file. Used for debugging."""
        super().Print_Targeted_Data(self.TARGET_DATA, number_of_lines)       

    class SQL_Data:
        def __init__(self):
            self.id = ""
            self.genre = ""
            self.fiction_or_non = ""

        def Set_Id(self, id):
            self.id = id

        def Process_Dict(self, cell : dict):
            if len(cell.keys()) == 0 :
                return # No data

            # Get fiction or non-fiction
            fiction_votes, non_fiction_votes = cell.get('fiction',0), cell.get('non-fiction',0)

            if fiction_votes > non_fiction_votes:
                self.fiction_or_non = "fiction"
            elif non_fiction_votes > fiction_votes:
                self.fiction_or_non = "non-fiction"
            else:
                self.fiction_or_non = ""

            # Removes fiction and non-fiction from the dictionary to process the genre
            cell.pop('fiction', None)
            cell.pop('non-fiction', None)


            if len(cell.keys()) == 0 :
                return # No genre data

            self.genre = max(cell, key=cell.get) # Gets the key of the entry with the highest int value

        def Convert_To_Array(self) -> list:
            return [self.fiction_or_non, self.genre, self.id]


    def Process_Line(self, data : dict):
        '''Uniquely processes the data and writes it to the SQL database. Passed as an argument into the super's write sql function'''
        # Using a dedicated class for this downloader's data allows perfect mapping to the sql statement, without worrying about
        # the order of fiction/non-fiction and sub-genre in the singular data set dictionary
        entry_data = self.SQL_Data()
        for key in self.TARGET_DATA:
            cell = data.get(key, "")
            if type(cell) == dict:
                entry_data.Process_Dict(cell)
            else:
                entry_data.Set_Id(cell)

        self.cursor.execute(self.sql_statement, entry_data.Convert_To_Array())

    
    def Write_SQL(self):
        # The goodreads id column needs to be indexed or else this is extremely slow
        self.Open_DB()
        print('Indexing goodreads_id...')
        sql_statement = 'CREATE INDEX IF NOT EXISTS idx_books_goodreads_id ON books(goodreads_id);'
        self.cursor.execute(sql_statement)
        self.db.commit()
        self.Close_DB()

        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        super().Write_SQL(self.Process_Line)

        # The goodreads_id index is no longer needed.
        self.Open_DB()
        print('Removing goodreads_id index...')
        sql_statement = 'DROP INDEX IF EXISTS idx_books_goodreads_id;'
        self.cursor.execute(sql_statement)
        self.db.commit()
        self.Close_DB()

class CompositeDownloader:
    def __init__(self):
        print('Downloading the database files...')
        self.downloaders = {
            'BookDownloader' : BookDownloader(),
            'AuthorDownloader' : AuthorDownloader(),
            'GenreDownloader' : GenreDownloader()
        }

    def Write_SQL(self):
        '''Downloads the book database files and converts them into a SQL database.'''
        print('Writing to the Database...')
        self.downloaders['BookDownloader'].Write_SQL()
        self.downloaders['AuthorDownloader'].Write_SQL()
        self.downloaders['GenreDownloader'].Write_SQL()

def Main():
    start_time = time.time()
    downloader = CompositeDownloader()
    downloader.Write_SQL()
    completion_time = time.time() - start_time
    print(f"Time taken to download and convert the database files: {completion_time} seconds")

# References https://docs.python.org/3.13/library/__main__.html
if __name__ == "__main__":
    Main()


