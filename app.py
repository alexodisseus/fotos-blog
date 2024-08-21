from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads
db = SQLAlchemy(app)

# Modelo de dados para Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    tag = db.Column(db.String(50), nullable=True)
    fotos = db.relationship('Foto', backref='post', lazy=True)

# Modelo de dados para Foto
class Foto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    caminho = db.Column(db.String(200), nullable=False)  # Caminho no servidor
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Inicialize o banco de dados manualmente
def init_db():
    with app.app_context():
        db.create_all()

# Inicializar o banco de dados
init_db()

@app.route('/posts')
def posts():
    all_posts = Post.query.all()
    return render_template('posts.html', posts=all_posts)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        titulo = request.form['titulo']
        texto = request.form['texto']
        data = datetime.strptime(request.form['data'], '%Y-%m-%d')
        tag = request.form['tag']
        
        # Cria um nome de pasta seguro
        safe_title = secure_filename(titulo).replace(' ', '_')
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_title)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Cria um novo post
        novo_post = Post(titulo=titulo, texto=texto, data=data, tag=tag)
        db.session.add(novo_post)
        db.session.commit()

        # Lidar com os arquivos de foto
        fotos = request.files.getlist('fotos')
        for i, foto in enumerate(fotos):
            if foto:
                filename = secure_filename(foto.filename)
                # Renomear a foto com a data e um número sequencial
                file_extension = os.path.splitext(filename)[1]
                new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{i + 1}{file_extension}"
                filepath = os.path.join(folder_path, new_filename)
                foto.save(filepath)

                # Criar uma nova entrada de foto no banco de dados
                caminho_relativo = os.path.join(safe_title, new_filename)
                nova_foto = Foto(nome=new_filename, caminho=caminho_relativo, post_id=novo_post.id)
                db.session.add(nova_foto)

        db.session.commit()
        return redirect(url_for('cadastro'))
    
    return render_template('cadastro.html')

if __name__ == '__main__':
    app.run(debug=True)
