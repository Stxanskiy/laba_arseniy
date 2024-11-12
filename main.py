from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import sqlite3
from hashlib import sha256

from kivy_garden.matplotlib import FigureCanvasKivyAgg
from matplotlib import pyplot as plt

from database   import init_db
from functools import partial
from datetime import datetime
import kivy_matplotlib_widget


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.username = TextInput(hint_text='Имя пользователя', multiline=False)
        self.password = TextInput(hint_text='Пароль', multiline=False, password=True)
        login_button = Button(text='Войти', on_press=self.login)
        register_button = Button(text='Создать аккаунт', on_press=partial(self.change_screen, 'registration'))

        layout.add_widget(Label(text='Авторизация'))
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_button)
        layout.add_widget(register_button)

        self.add_widget(layout)

    def login(self, instance):
        username = self.username.text
        password = sha256(self.password.text.encode()).hexdigest()

        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            if user[0] == 'admin':
                self.manager.current = 'admin_screen'
            else:
                self.manager.current = 'user_screen'
        else:
            self.username.text = ''
            self.password.text = ''
            self.add_widget(Label(text='Неверные данные!'))

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name


from functools import partial

class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.username = TextInput(hint_text='Имя пользователя', multiline=False)
        self.password = TextInput(hint_text='Пароль', multiline=False, password=True)
        self.secret_question = TextInput(hint_text='Секретный вопрос', multiline=False)
        self.secret_answer = TextInput(hint_text='Ответ на секретный вопрос', multiline=False)

        register_button = Button(text='Зарегистрироваться', on_press=self.register)
        back_button = Button(text='Назад', on_press=partial(self.change_screen, 'login'))

        layout.add_widget(Label(text='Регистрация'))
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(self.secret_question)
        layout.add_widget(self.secret_answer)
        layout.add_widget(register_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def register(self, instance):
        username = self.username.text
        password = sha256(self.password.text.encode()).hexdigest()
        secret_question = self.secret_question.text
        secret_answer = self.secret_answer.text

        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password, role, secret_question, secret_answer)
                VALUES (?, ?, 'user', ?, ?)
            """, (username, password, secret_question, secret_answer))
            conn.commit()
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            self.add_widget(Label(text='Пользователь уже существует!'))
        finally:
            conn.close()

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name

class PasswordRecoveryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.username = TextInput(hint_text='Имя пользователя', multiline=False)
        self.secret_question = Label(text='Секретный вопрос:')
        self.secret_answer = TextInput(hint_text='Ответ на секретный вопрос', multiline=False)
        self.new_password = TextInput(hint_text='Новый пароль', multiline=False, password=True)

        recovery_button = Button(text='Восстановить пароль', on_press=self.recover_password)
        back_button = Button(text='Назад', on_press=partial(self.change_screen, 'login'))

        layout.add_widget(Label(text='Восстановление пароля'))
        layout.add_widget(self.username)
        layout.add_widget(self.secret_question)
        layout.add_widget(self.secret_answer)
        layout.add_widget(self.new_password)
        layout.add_widget(recovery_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def recover_password(self, instance):
        username = self.username.text
        answer = self.secret_answer.text
        new_password = sha256(self.new_password.text.encode()).hexdigest()

        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT secret_question, secret_answer FROM users WHERE username=?
        """, (username,))
        user = cursor.fetchone()

        if user and user[1] == answer:
            cursor.execute("""
                UPDATE users SET password=? WHERE username=?
            """, (new_password, username))
            conn.commit()
            self.manager.current = 'login'
        else:
            self.add_widget(Label(text='Неверный ответ на секретный вопрос!'))
        conn.close()

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name


class TransactionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.type = TextInput(hint_text='Тип (income/expense)', multiline=False)
        self.amount = TextInput(hint_text='Сумма', multiline=False)
        self.category = TextInput(hint_text='Категория', multiline=False)

        add_button = Button(text='Добавить транзакцию', on_press=self.add_transaction)
        back_button = Button(text='Назад', on_press=partial(self.change_screen, 'user_screen'))

        layout.add_widget(Label(text='Добавление транзакции'))
        layout.add_widget(self.type)
        layout.add_widget(self.amount)
        layout.add_widget(self.category)
        layout.add_widget(add_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def add_transaction(self, instance):
        transaction_type = self.type.text
        amount = float(self.amount.text)
        category = self.category.text

        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, category, date)
            VALUES (?, ?, ?, ?, DATE('now'))
        """, (1, transaction_type, amount, category))  # user_id = 1 для примера
        conn.commit()
        conn.close()

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name




class UserScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.greeting = Label(text='Добро пожаловать, пользователь!')
        add_transaction_btn = Button(text='Добавить транзакцию', on_press=partial(self.change_screen, 'add_transaction'))
        view_transactions_btn = Button(text='Просмотреть транзакции', on_press=partial(self.change_screen, 'view_transactions'))
        view_balance_btn = Button(text='Просмотреть баланс', on_press=self.view_balance)
        back_btn = Button(text='Выйти', on_press=partial(self.change_screen, 'login'))

        layout.add_widget(self.greeting)
        layout.add_widget(add_transaction_btn)
        layout.add_widget(view_transactions_btn)
        layout.add_widget(view_balance_btn)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name

    def view_balance(self, instance):
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) 
            FROM transactions 
            WHERE user_id = ?
        """, (1,))  # Здесь 1 замените на текущего пользователя
        balance = cursor.fetchone()[0]
        conn.close()

        balance_label = Label(text=f'Текущий баланс: {balance:.2f}' if balance else 'Баланс: 0.00')
        self.add_widget(balance_label)

class AdminScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        view_users_btn = Button(text='Просмотреть пользователей', on_press=partial(self.change_screen, 'view_users'))
        view_all_transactions_btn = Button(text='Просмотреть все транзакции', on_press=partial(self.change_screen, 'view_all_transactions'))
        back_btn = Button(text='Выйти', on_press=partial(self.change_screen, 'login'))
        view_graphs_btn = Button(text='Просмотреть графики', on_press=partial(self.change_screen, 'view_graphs'))
        layout.add_widget(view_graphs_btn)

        layout.add_widget(Label(text='Администратор'))
        layout.add_widget(view_users_btn)
        layout.add_widget(view_all_transactions_btn)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name

class ViewTransactionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.transactions_label = Label(text='Список транзакций:')
        back_btn = Button(text='Назад', on_press=partial(self.change_screen, 'user_screen'))

        layout.add_widget(self.transactions_label)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def on_enter(self):
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, amount, category, date 
            FROM transactions 
            WHERE user_id = ?
        """, (1,))  # Здесь 1 замените на текущего пользователя
        transactions = cursor.fetchall()
        conn.close()

        transactions_text = "\n".join([f"{t[0]}: {t[1]:.2f} руб., {t[2]} ({t[3]})" for t in transactions])
        self.transactions_label.text = transactions_text if transactions else "Нет транзакций"

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name

class ViewAllTransactionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.transactions_label = Label(text='Список всех транзакций:')
        self.delete_transaction_button = Button(text='Удалить транзакцию', on_press=self.delete_transaction)
        back_btn = Button(text='Назад', on_press=partial(self.change_screen, 'admin_screen'))

        layout.add_widget(self.transactions_label)
        layout.add_widget(self.delete_transaction_button)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def on_enter(self):
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, u.username, t.type, t.amount, t.category, t.date 
            FROM transactions t
            JOIN users u ON t.user_id = u.id
        """)
        self.transactions = cursor.fetchall()
        conn.close()

        transactions_text = "\n".join(
            [f"{t[0]}. {t[1]} - {t[2]}: {t[3]:.2f} руб., {t[4]} ({t[5]})" for t in self.transactions])
        self.transactions_label.text = transactions_text if self.transactions else "Нет транзакций"

    def delete_transaction(self, instance):
        if not self.transactions:
            return

        self.delete_transaction_button.text = "Вы уверены, что хотите удалить эту транзакцию?"
        self.delete_transaction_button.on_press = self.confirm_delete_transaction

    def confirm_delete_transaction(self, instance):
        transaction_to_delete = self.transactions[0]  # Для примера выбираем первую транзакцию
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_to_delete[0],))
        conn.commit()
        conn.close()

        self.on_enter()  # Обновляем список транзакций после удаления
        self.delete_transaction_button.text = "Удалить транзакцию"
        self.delete_transaction_button.on_press = self.delete_transaction  # Сбрасываем кнопку

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name

class ViewUsersScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.users_label = Label(text='Список пользователей:')
        self.delete_user_button = Button(text='Удалить пользователя', on_press=self.delete_user)
        back_btn = Button(text='Назад', on_press=partial(self.change_screen, 'admin_screen'))

        layout.add_widget(self.users_label)
        layout.add_widget(self.delete_user_button)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def on_enter(self):
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        self.users = cursor.fetchall()
        conn.close()

        users_text = "\n".join([f"{u[0]}. {u[1]} ({u[2]})" for u in self.users])
        self.users_label.text = users_text if self.users else "Нет зарегистрированных пользователей"

    def delete_user(self, instance):
        if not self.users:
            return

        # Вопрос о подтверждении удаления
        self.delete_user_button.text = "Вы уверены, что хотите удалить этого пользователя?"
        self.delete_user_button.on_press = self.confirm_delete

    def confirm_delete(self, instance):
        user_to_delete = self.users[0]  # Для примера выбираем первого пользователя (потом можно будет улучшить)
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=?", (user_to_delete[0],))
        conn.commit()
        conn.close()

        self.on_enter()  # Обновляем список пользователей после удаления
        self.delete_user_button.text = "Удалить пользователя"
        self.delete_user_button.on_press = self.delete_user  # Сбрасываем кнопку

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name

class ViewGraphsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        # Поля для фильтрации по датам
        filter_layout = BoxLayout(size_hint=(1, 0.2))
        self.start_date = TextInput(hint_text='Дата начала (YYYY-MM-DD)', multiline=False)
        self.end_date = TextInput(hint_text='Дата конца (YYYY-MM-DD)', multiline=False)
        apply_filter_btn = Button(text='Применить фильтр', on_press=self.apply_filter)

        filter_layout.add_widget(self.start_date)
        filter_layout.add_widget(self.end_date)
        filter_layout.add_widget(apply_filter_btn)

        # Раздел для графика
        self.chart_layout = BoxLayout(size_hint=(1, 0.6))
        self.update_chart()  # Построение графика при загрузке экрана

        back_btn = Button(text='Назад', size_hint=(1, 0.2), on_press=partial(self.change_screen, 'admin_screen'))

        layout.add_widget(filter_layout)
        layout.add_widget(self.chart_layout)
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def update_chart(self, start_date=None, end_date=None):
        conn = sqlite3.connect("finance_manager.db")
        cursor = conn.cursor()

        # Базовый SQL-запрос
        query = """
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE type = 'expense' 
        """
        params = []

        # Условия для фильтрации по датам
        if start_date and end_date:
            query += "AND date BETWEEN ? AND ? "
            params.extend([start_date, end_date])

        query += "GROUP BY category"
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()

        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]

        plt.clf()  # Очищаем предыдущий график
        plt.bar(categories, amounts, color='blue')
        plt.title('Расходы по категориям')
        plt.xlabel('Категории')
        plt.ylabel('Сумма')

        self.chart_layout.clear_widgets()
        self.chart_layout.add_widget(FigureCanvasKivyAgg(plt.gcf()))

    def apply_filter(self, instance):
        try:
            start_date = datetime.strptime(self.start_date.text, '%Y-%m-%d').strftime('%Y-%m-%d')
            end_date = datetime.strptime(self.end_date.text, '%Y-%m-%d').strftime('%Y-%m-%d')
            self.update_chart(start_date, end_date)
        except ValueError:
            self.start_date.text = ''
            self.end_date.text = ''
            self.add_widget(Label(text='Неверный формат даты!'))

    def change_screen(self, screen_name, instance):
        self.manager.current = screen_name



class FinanceApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegistrationScreen(name='registration'))
        sm.add_widget(PasswordRecoveryScreen(name='password_recovery'))
        sm.add_widget(TransactionScreen(name='add_transaction'))
        sm.add_widget(UserScreen(name='user_screen'))
        sm.add_widget(AdminScreen(name='admin_screen'))
        sm.add_widget(ViewUsersScreen(name='view_users'))
        sm.add_widget(ViewAllTransactionsScreen(name='view_all_transactions'))
        sm.add_widget(ViewTransactionsScreen(name='view_transactions'))
        return sm





if __name__ == "__main__":
    init_db()
    FinanceApp().run()
