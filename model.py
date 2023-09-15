import sqlite3
import random
import openai
import bcrypt


class Model:
    def __init__(self):
        self.conn = sqlite3.connect("data.db")
        self.curs = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.__key = "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"

        self._create_table()

    def _create_table(self) -> None:
        self.curs.execute("""CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT)
                """)

        self.curs.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            username TEXT,
            passwd TEXT,
            best_result INTEGER)
        """)

        self.curs.execute("""CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            category_id INTEGER NOT NULL,
            question TEXT,
            correct_answer TEXT,
            wrong_one TEXT,
            wrong_two TEXT,
            wrong_three TEXT,
            level INTEGER,
            author TEXT NOT NULL,
            correct_answers INTEGER,
            incorrect_answers INTEGER,
            FOREIGN KEY(category_id) REFERENCES categories(id))
        """)

        self.curs.execute("""CREATE TABLE IF NOT EXISTS users_questions (
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT,
            correct_or_not BOOL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(question_id) REFERENCES questions(id))
        """)

        self.curs.execute("""CREATE TABLE IF NOT EXISTS results (
            user_id INTEGER NOT NULL,
            result INTEGER,
            category_id INTEGER NOT NULL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(category_id) REFERENCES categories(id))
        """)

        self.conn.commit()

    def save_results(self, user_id, result, category, date):
        self.curs.execute(f"SELECT id FROM categories WHERE category = '{category}'")
        category_id = self.curs.fetchone()[0]
        self.curs.execute(f"INSERT INTO results (user_id, result, category_id, date) "
                          f"VALUES ('{user_id}', '{result}', '{category_id}', '{date}')")
        self.conn.commit()

    def save_question(self, user_num, question, answer, correct_or_not, date):
        self.curs.execute(f"SELECT id FROM questions WHERE question = '{question}'")
        question_num = self.curs.fetchone()[0]
        self.curs.execute(f"INSERT INTO users_questions (user_id, question_id, answer, correct_or_not, date) "
                          "VALUES (?, ?, ?, ?, ?)",
                          (user_num, question_num, answer, correct_or_not, date))
        self.conn.commit()

    def ask_chat_gpt(self, question):
        openai.api_key = self.__key
        messages = [{"role": "system", "content": "You are a friend of mine."}]
        message = f"{question} Answer in one sentence."
        messages.append({"role": "user", "content": message})
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        reply = chat.choices[0].message.content

        return reply

    def get_user(self, user) -> tuple:
        self.curs.execute("SELECT * FROM users WHERE username = ?", (user,))
        return self.curs.fetchone()

    def registration(self, first_name, last_name, email, username, passwd, best_result=0) -> str:
        self.curs.execute("SELECT username FROM users")
        users = self.curs.fetchall()

        if len(first_name) < 3:
            return "Your First name must be at least 3 characters"
        elif len(last_name) < 3:
            return "Your Last name must be at least 3 characters"
        elif '@' not in email:
            return "Your email must contain '@'"
        elif len(username) < 3:
            return "Your username must be at least 3 characters"
        elif username in users:
            return "This username already exist"
        elif len(passwd) < 6:
            return "Your password must be at least 6 characters"

        passwd = passwd.encode("utf-8")
        hash_pass = bcrypt.hashpw(passwd, bcrypt.gensalt())

        insert_command = "INSERT INTO users (first_name, last_name, email, username, passwd, best_result) " \
                         "VALUES (?,?,?,?,?,?)"
        self.curs.execute(insert_command, (first_name, last_name, email, username, hash_pass, best_result))
        self.conn.commit()

        return "OK"

    def get_questions(self, category) -> list:
        self.curs.execute("SELECT id FROM categories WHERE category = ?", (category,))
        category = self.curs.fetchone()[0]

        self.curs.execute("SELECT * FROM questions WHERE level = 1 and category_id = ?", (category,))
        first_level = self.curs.fetchall()

        self.curs.execute("SELECT * FROM questions WHERE level = 2 and category_id = ?", (category,))
        second_level = self.curs.fetchall()

        self.curs.execute("SELECT * FROM questions WHERE level = 3 and category_id = ?", (category,))
        third_level = self.curs.fetchall()

        selected_first = set()
        selected_second = set()
        selected_third = set()

        while len(selected_first) < 5:
            selected_first.add(random.choice(first_level))

        while len(selected_second) < 5:
            selected_second.add(random.choice(second_level))

        while len(selected_third) < 5:
            selected_third.add(random.choice(third_level))

        result = []
        result.extend(selected_first)
        result.extend(selected_second)
        result.extend(selected_third)

        return result

    # def add_question(self, category):
    #     insert_command = "INSERT INTO questions " \
    #                      "(category, question, correct_answer, wrong_one, wrong_two, wrong_three, level) " \
    #                      "VALUES (?,?,?,?,?,?,?)"
    #     self.curs.execute(insert_command, (
    #         "python",
    #         "What is the difference between an iterator and a generator in Python?",
    #         "An iterator is an object that can be iterated over, while a generator is a special type of iterator that is defined using a function with the yield keyword",
    #         "An iterator is a class that defines how objects can be iterated over, while a generator is a function that returns an iterable object",
    #         "An iterator generates a sequence of values lazily, while a generator returns an iterator",
    #         "An iterator is a function that returns an iterable object, while a generator is an object that can be iterated over",
    #         3
    #     ))
    #     self.conn.commit()

    def check_user_and_password(self, user, passwd) -> str:
        self.curs.execute("SELECT * FROM users WHERE username = ?", (user,))
        user = self.curs.fetchone()

        if not user:
            return "User not found"
        elif not bcrypt.checkpw(passwd.encode("utf-8"), user[-2]):
            return "Password is incorrect"
        else:
            return "OK"

    def get_category_list(self) -> set:
        self.curs.execute("SELECT category FROM categories")
        result = set()
        for row in self.curs.fetchall():
            result.add(row[0])
        return result

    def get_user_results(self, username) -> list:
        self.curs.execute(f"SELECT id FROM users WHERE username = '{username}'")
        user_id = self.curs.fetchone()[0]
        self.curs.execute("SELECT * FROM results WHERE user_id = ?", (user_id,))

        return self.curs.fetchall()

    def close_connection(self) -> None:
        self.conn.close()
