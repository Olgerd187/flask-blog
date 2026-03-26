import sqlite3
from flask import Flask, render_template
from werkzeug.exceptions import abort

def get_db_connection():
    """
    Создает подключение к базе данных SQLite.
    Устанавливает row_factory для доступа к столбцам по именам.
    """
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # позволяет обращаться к столбцам по именам
    return conn

def get_post(post_id):
    """
    Получает пост из базы данных по его ID.
    Если пост не найден, возвращает 404 ошибку.
    """
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)  # возвращает страницу 404 Not Found
    return post

app = Flask(__name__)

@app.route('/')
def index():
    """
    Главная страница: отображает список всех постов.
    """
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/<int:post_id>')
def post(post_id):
    """
    Страница отдельного поста: отображает содержимое поста с указанным ID.
    """
    post = get_post(post_id)
    return render_template('post.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)

from flask import request, url_for, flash, redirect

app.config['SECRET_KEY'] = 'your secret key'

@app.route('/create', methods=('GET', 'POST'))
def create():
    """
    Страница создания нового поста.
    GET: отображает форму
    POST: обрабатывает отправку формы и сохраняет пост в БД
    """
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    """
    Страница редактирования поста.
    GET: отображает форму с текущими данными
    POST: сохраняет изменения в БД
    """
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE posts SET title = ?, content = ?'
                        ' WHERE id = ?',
                        (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    """
    Удаление поста.
    Принимает только POST-запросы (нельзя удалить просто перейдя по ссылке).
    """
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('index'))
