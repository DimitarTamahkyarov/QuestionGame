from datetime import datetime
import random
from kivy.app import App
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.list import TwoLineListItem
from model import Model


class ChatGPT(Popup):
    pass


class WelcomeWindow(Screen):
    pass


class RegisterWindow(Screen):
    def check_registration_is_valid(self) -> bool:

        first_name = self.ids.first_name.text
        last_name = self.ids.last_name.text
        email = self.ids.email.text
        username = self.ids.username.text
        passwd = self.ids.passwd.text
        conf_passwd = self.ids.conf_passwd.text

        response = "Password not confirmed!"

        if passwd == conf_passwd:
            response = App.get_running_app().registration(first_name, last_name, email, username, passwd)

        if response != "OK":
            self.ids.error.text = response
            return False
        else:
            game.update_logged_user(username)
            return True


class LoginWindow(Screen):
    def check_username_and_password(self) -> bool:
        username = self.ids.username.text
        passwd = self.ids.passwd.text

        response = game.login(username, passwd)

        if response != "OK":
            self.ids.error.text = response
            return False
        else:
            game.update_logged_user(username)
            return True


class DashboardWindow(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories = None
        self.logged_user = None

    def say_hello(self) -> None:
        self.logged_user = game.get_logged_user()
        first_name = self.logged_user[1]
        last_name = self.logged_user[2]
        self.ids.welcome.text = f"Welcome {first_name} {last_name}! "

    def update_spinner(self) -> None:
        self.categories = game.get_category_list()
        self.ids.spinner_id.values = self.categories

    def update_category(self, category) -> None:
        game.category = category

    def start_button_clicked(self) -> None:
        if self.ids.spinner_id.text != "Click here to select category":
            self.manager.current = "game_window"
            self.ids.error_message.text = ""
        else:
            self.ids.error_message.text = "Incorrect category!"


class GameWindow(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer_func = None
        self.questions = []
        self.correct_answer = None
        self.index = 0
        self.total_timer = 0
        self.total_score = 0
        self.labels = []

    def set_game(self):
        self.ids.timer.text = "30"
        self.index = 0
        self.ids.button_one.disabled = True
        self.ids.button_two.disabled = True
        self.ids.button_three.disabled = True
        self.ids.button_four.disabled = True
        self.ids.halving.disabled = True
        self.ids.GPT.disabled = True
        self.ids.quit.disabled = True

        self.ids.question.text = ""
        self.ids.button_one.text = ""
        self.ids.button_two.text = ""
        self.ids.button_three.text = ""
        self.ids.button_four.text = ""

    def get_questions(self) -> None:
        try:
            self.questions = game.get_questions()
        finally:
            self.labels = [self.ids.one, self.ids.two, self.ids.three, self.ids.four, self.ids.five, self.ids.six,
                           self.ids.seven, self.ids.eight, self.ids.nine, self.ids.ten, self.ids.eleven,self.ids.twelve,
                           self.ids.thirteen, self.ids.fourteen, self.ids.fifteen]

        self.ids.start.disabled = False

    def start_game(self) -> None:
        self.ids.halving.disabled = False
        self.ids.GPT.disabled = False
        self.ids.quit.disabled = False

    def update_labels(self) -> None:
        self.timer_running()
        self.ids.start.disabled = True
        self.correct_answer = self.questions[self.index][3]
        self.ids.question.text = self.questions[self.index][2]
        self.ids.button_one.disabled = False
        self.ids.button_two.disabled = False
        self.ids.button_three.disabled = False
        self.ids.button_four.disabled = False

        answers = set()
        while len(answers) < 4:
            answers.add(random.choice(self.questions[self.index][3:7]))

        answers = list(answers)

        self.ids.button_one.text = answers[0]
        self.ids.button_two.text = answers[1]
        self.ids.button_three.text = answers[2]
        self.ids.button_four.text = answers[3]

        with self.labels[self.index].canvas.before:
            Color(252/255, 140/255, 3/255, 1)
            Rectangle(pos=self.labels[self.index].pos, size=self.labels[self.index].size)

        try:
            with self.labels[self.index-1].canvas.before:
                Color(0, 0, 0, 0.8)
                Rectangle(pos=self.labels[self.index-1].pos, size=self.labels[self.index-1].size)
        except IndexError:
            pass

        if self.index == 5:
            with self.ids.first_level.canvas.before:
                Color(52 / 255, 235 / 255, 52 / 255, 1)
                Rectangle(pos=self.ids.first_level.pos, size=self.ids.first_level.size)
        elif self.index == 10:
            with self.ids.second_level.canvas.before:
                Color(52 / 255, 235 / 255, 52 / 255, 1)
                Rectangle(pos=self.ids.second_level.pos, size=self.ids.second_level.size)

        self.index += 1

    def timer_running(self) -> None:
        self.timer_func = Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, *args) -> None:
        if int(self.ids.timer.text) > 0:
            self.ids.timer.text = str(int(self.ids.timer.text) - 1)
            self.total_timer += 1
        else:
            self.timer_func.cancel()
            self.quit()

    def button_clicked(self, text) -> None:
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        if text == self.correct_answer:
            self.timer_func.cancel()
            self.ids.timer.text = "30"
            self.update_labels()
            if self.index < 5:
                self.total_score += 100
            elif self.index < 10:
                self.total_score += 150
            else:
                self.total_score += 200
            App.get_running_app().save_question(self.ids.question.text, text, True, current_date)
        else:
            App.get_running_app().save_question(self.ids.question.text, text, False, current_date)
            self.quit()

    def get_response(self):
        question = self.ids.question.text
        response = game.ask_chat_GPT(question)
        popup = ChatGPT()
        popup.ids.message.text = response
        popup.open()
        self.ids.timer.text = str(int(self.ids.timer.text) + 30)

        return response

    def halving(self):

        buttons = []

        if self.ids.button_one.text != self.correct_answer:
            buttons.append(self.ids.button_one)
        if self.ids.button_two.text != self.correct_answer:
            buttons.append(self.ids.button_two)
        if self.ids.button_three.text != self.correct_answer:
            buttons.append(self.ids.button_three)
        if self.ids.button_four.text != self.correct_answer:
            buttons.append(self.ids.button_four)

        buttons.remove(random.choice(buttons))

        for button in buttons:
            button.disabled = True

        self.ids.halving.disabled = True
        self.ids.timer.text = str(int(self.ids.timer.text) + 30)

    def quit(self) -> None:
        self.timer_func.cancel()
        if self.ids.timer.text == "0":
            if self.index >= 10:
                self.total_score = 500 + 750
            elif self.index >= 5:
                self.total_score = 500

        self.total_score -= self.total_timer
        game.current_result = self.total_score if self.total_score >= 0 else 0
        self.ids.timer.text = "0"
        self.manager.current = "game_over_window"
        self.manager.transition.direction = "left"
        App.get_running_app().save_result()


class GameOverWindow(Screen):
    def get_user_results(self):
        data = game.get_user_results()

        for i in range(len(data)-1, -1, -1):
            row = data[i]

            item = TwoLineListItem(
                text=f'Result: {row[1]}',
                secondary_text=f"Date: {row[3]}"
            )
            self.ids.result_list.add_widget(item)


class WindowManager(ScreenManager):
    pass


class QuestionApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = Model()
        self.logged_user = None
        self.category = None
        self.current_result = 0
        self.sound = SoundLoader.load("Elevator-music(chosic.com).mp3")
        self.sound.play()

    def build(self):
        self.title = 'The Game of Questions'
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepOrange"
        return Builder.load_file('view.kv')

    def registration(self, first_name, last_name, email, username, passwd):
        return self.model.registration(first_name, last_name, email, username, passwd)

    def login(self, user_input, password_input) -> str:
        return self.model.check_user_and_password(user_input, password_input)

    def update_logged_user(self, username):
        self.logged_user = self.model.get_user(username)

    def get_category_list(self):
        return self.model.get_category_list()

    def get_logged_user(self):
        return self.logged_user

    def get_questions(self):
        return self.model.get_questions(self.category)

    def save_question(self, question, answer, correct_or_not, date) -> None:
        user = self.logged_user
        self.model.save_question(user[0], question, answer, correct_or_not, date)

    def ask_chat_GPT(self, question):
        return self.model.ask_chat_gpt(question)

    def save_result(self) -> None:
        user = self.logged_user
        result = self.current_result
        category = self.category
        date = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.model.save_results(user[0], result, category, date)

    def get_user_results(self):
        return self.model.get_user_results(self.logged_user[4])


if __name__ == "__main__":
    game = QuestionApp()
    game.run()
    game.model.close_connection()

