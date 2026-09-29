# Designed by Ryan Pettinger
# Qwen2.5 Coder 1.5b was utilized for autocomplete functionality
# 9/29/26

# Data sets are courtsey of the University of California, San Diego
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

    def OpenDB(self, flush_existing : bool = False):
        '''Opens a SQLite3 DB in the class specified directory'''
        self.db = sqlite3.connect(self.Get_DB_Path())
        self.cursor = self.db.cursor()
        print('DB is open')
        if (flush_existing):
            self.cursor.execute("DROP TABLE IF EXISTS books;")
            self.cursor.execute("""CREATE TABLE books (
                database_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goodreads_id INTEGER,
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

    def CloseDB(self):
        '''Closes the SQLite3 DB in the classy'''
        if self.db is not None:
            self.cursor.close()
            self.db.close()
            print('DB is closed')
        else:
            print('DB was not open.')

    def Write_SQL(self, processLine : function, commit_after : int = 5000, flush_existing : bool = False):
        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        self.OpenDB(flush_existing)
        # Iterate through every line, writing to the sqlite3 database
            
        with gzip.open(self.Get_File_Path(), 'rb') as file:
            counter : float = 0
            EXECUTE_COUNTER, current_execute_counter = commit_after, 0
            
            for line in file:
                counter += 1
                print(f'Processing line: {counter}', end='\r')
                data = json.loads(line)
                            
                processLine(data)
            
                current_execute_counter += 1
                if current_execute_counter >= EXECUTE_COUNTER:
                    current_execute_counter = 0
                    self.db.commit()

            # Final commit if last batch is less than 5k
            self.db.commit()
            print('\nDone writing to DB')

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
            '''Uniquely processes the data and writes it to the SQL database. Passed as an argument into the parents's write sql function'''
            entry_data = []
            for key in self.TARGET_DATA:
                cell = data.get(key, "")

                if type(cell) == list:
                    if (len(cell) > 1):
                        cell = "" # No recorded author
                    elif (len(cell) == 0):
                        cell = "-1" # This will represent multiple authors
                    else:
                        cell = cell[0].get('author_id','')

                entry_data.append(cell)

            self.cursor.execute(self.sql_statement, entry_data)

    def Write_SQL(self):
        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        super().Write_SQL(self.ProcessLine, flush_existing=True) # Drops the existing database before adding the new entries


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

    def ProcessLine(self, data : dict):
        '''Uniquely processes the data and writes it to the SQL database. Passed as an argument into the super's write sql function'''
        entry_data = []
        for key in self.TARGET_DATA:
            cell = data.get(key, "")
            entry_data.append(cell)
        self.cursor.execute(self.sql_statement, entry_data)

    def Write_SQL(self):
        # The author id column needs to be indexed or else this is extremely slow
        super().OpenDB()
        print('Indexing author_id...')
        sql_statement = 'CREATE INDEX IF NOT EXISTS idx_books_author_id ON books(author_id);'
        self.cursor.execute(sql_statement)
        self.db.commit()
        super().CloseDB()

        super().Write_SQL(self.ProcessLine)

        # The author_id index is no longer needed.
        super().OpenDB()
        print('Removing goodreads_id index...')
        sql_statement = 'DROP INDEX IF EXISTS idx_books_author_id;'
        self.cursor.execute(sql_statement)
        self.db.commit()
        super().CloseDB()

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

    class sql_data:
        def __init__(self):
            self.id = "",
            self.genre = ""
            self.fiction_or_non = ""

        def SetId(self, id):
            self.id = id

        def ProcessDict(self, cell : dict):
            if len(cell.keys()) == 0 :
                return # No data

            # Get fiction or non-fiction
            fiction_votes, non_fiction_votes = cell.get('fiction',0), cell.get('non-fiction',0)
            self.fiction_or_non = "fiction" if fiction_votes > non_fiction_votes else "non-fiction"
            # Removes fiction and non-fiction from the dictionary to process the genre
            cell.pop('fiction', None)
            cell.pop('non-fiction', None)


            if len(cell.keys()) == 0 :
                return # No genre data

            self.genre = max(cell, key=cell.get) # Gets the key of the entry with the highest int value

        def ConvertToArray(self) -> list:
            return [self.fiction_or_non, self.genre, self.id]


    def ProcessLine(self, data : dict):
        '''Uniquely processes the data and writes it to the SQL database. Passed as an argument into the super's write sql function'''
        entry_data = self.sql_data()
        for key in self.TARGET_DATA:
            cell = data.get(key, "")
            if type(cell) == dict:
                entry_data.ProcessDict(cell)
            else:
                entry_data.SetId(cell)

        self.cursor.execute(self.sql_statement, entry_data.ConvertToArray())

    
    def Write_SQL(self):
        # The goodreads id column needs to be indexed or else this is extremely slow
        super().OpenDB()
        print('Indexing goodreads_id...')
        sql_statement = 'CREATE INDEX IF NOT EXISTS idx_books_goodreads_id ON books(goodreads_id);'
        self.cursor.execute(sql_statement)
        self.db.commit()
        super().CloseDB()

        '''Write the appropriate values to the SQL database using the child's specific processing function'''
        super().Write_SQL(self.ProcessLine)

        # The goodreads_id index is no longer needed.
        super().OpenDB()
        print('Removing goodreads_id index...')
        sql_statement = 'DROP INDEX IF EXISTS idx_books_goodreads_id;'
        self.cursor.execute(sql_statement)
        self.db.commit()
        super().CloseDB()

class CompositeDownloader:
    def __init__(self):
        print('Downloading the database files...')
        self.downloaders = {
            'BookDownloader' : BookDownloader(),
            'AuthorDownloader' : AuthorDownloader(),
            'GenreDownloader' : GenreDownloader()
        }

    def Write_SQL(self):
        '''Downloads the book database files and converts them into a SQL database. Returns the time it took to complete the process.'''
        print('Writting to the Database...')
        self.downloaders['BookDownloader'].Write_SQL()
        self.downloaders['AuthorDownloader'].Write_SQL()
        self.downloaders['GenreDownloader'].Write_SQL()

def main():
    start_time = time.time()
    downloader = CompositeDownloader()
    downloader.Write_SQL()
    completion_time = time.time() - start_time
    print(f"Time taken to download and convert the database files: {completion_time} seconds")

main()


