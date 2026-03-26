import sqlite3
import os
import uuid
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from PIL import Image

UPLOAD_FOLDER = 'static/uploads'
THUMBNAIL_FOLDER = 'static/thumbnails'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024
THUMBNAIL_SIZE = (300, 200)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_thumbnail(filepath, thumbpath):
    try:
        img = Image.open(filepath)
        img.thumbnail(THUMBNAIL_SIZE)
        img.save(thumbpath)
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    conn.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('index.html', posts=posts, page=page, total_pages=total_pages)

@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('image')
        if not title:
            flash('Title is required!')
        else:
            image_filename = None
            if file and allowed_file(file.filename):
                original_name = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(filepath)
                thumb_filename = f"thumb_{unique_name}"
                thumbpath = os.path.join(app.config['THUMBNAIL_FOLDER'], thumb_filename)
                if create_thumbnail(filepath, thumbpath):
                    image_filename = unique_name
                else:
                    image_filename = unique_name
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content, image) VALUES (?, ?, ?)', (title, content, image_filename))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('image')
        if not title:
            flash('Title is required!')
        else:
            image_filename = post['image']
            if file and allowed_file(file.filename):
                if post['image']:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], post['image'])
                    old_thumb = os.path.join(app.config['THUMBNAIL_FOLDER'], f"thumb_{post['image']}")
                    if os.path.exists(old_path): os.remove(old_path)
                    if os.path.exists(old_thumb): os.remove(old_thumb)
                original_name = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(filepath)
                thumb_filename = f"thumb_{unique_name}"
                thumbpath = os.path.join(app.config['THUMBNAIL_FOLDER'], thumb_filename)
                if create_thumbnail(filepath, thumbpath):
                    image_filename = unique_name
                else:
                    image_filename = unique_name
            conn = get_db_connection()
            conn.execute('UPDATE posts SET title = ?, content = ?, image = ? WHERE id = ?', (title, content, image_filename, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    if post['image']:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], post['image'])
        thumbpath = os.path.join(app.config['THUMBNAIL_FOLDER'], f"thumb_{post['image']}")
        if os.path.exists(filepath): os.remove(filepath)
        if os.path.exists(thumbpath): os.remove(thumbpath)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash(f'"{post["title"]}" was successfully deleted!')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM posts WHERE title LIKE ? OR content LIKE ?", (f'%{query}%', f'%{query}%')).fetchone()[0]
    posts = conn.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY created DESC LIMIT ? OFFSET ?",
                         (f'%{query}%', f'%{query}%', per_page, offset)).fetchall()
    conn.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('search_results.html', posts=posts, query=query, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)
