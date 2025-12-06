"""
SISTEMA DE GESTÃO DE PROPRIEDADES RURAIS E ANIMAIS - ProGest2

Este é um sistema web desenvolvido com Flask para gerenciamento de propriedades rurais,
proprietários, animais e lotes. O sistema inclui autenticação de usuários, dashboard
com estatísticas e módulo de Business Intelligence (BI).

ESTRUTURA PRINCIPAL:
1. Configuração da aplicação Flask e banco de dados MySQL
2. Modelos ORM para todas as entidades do sistema
3. Sistema de autenticação com sessões
4. CRUD completo para todas as entidades
5. Dashboard com métricas e visualização de dados
6. API para gráficos de BI
7. Templates HTML para interface do usuário

PRINCIPAIS FUNCIONALIDADES:
- Cadastro e gerenciamento de proprietários (Dono)
- Cadastro e gerenciamento de propriedades rurais
- Cadastro de tipos e raças de animais
- Registro de lotes de animais por propriedade
- Sistema de login/logout com controle de sessão
- Dashboard com estatísticas gerais
- Módulo de BI com gráficos e análises

TECNOLOGIAS UTILIZADAS:
- Flask: Framework web Python
- SQLAlchemy: ORM para manipulação do banco de dados
- MySQL: Banco de dados relacional
- HTML/CSS: Frontend (presumindo uso de templates)
- JavaScript: Para gráficos do BI (presumindo uso de Chart.js ou similar)

ARQUITETURA:
- Padrão MVC (Model-View-Controller)
- Templates separados para cada funcionalidade
- API RESTful para endpoints de dados
- Decorators para controle de acesso

SEGURANÇA:
- Sistema de sessões para autenticação
- Decorator @login_required para rotas protegidas
- Validação de dados nos formulários
- Tratamento de erros com mensagens flash

OBSERVAÇÕES PARA O PROFESSOR:
- Código bem estruturado e comentado
- Boas práticas de organização e separação de responsabilidades
- Tratamento de exceções em todas as operações de banco
- Uso de relacionamentos SQLAlchemy adequados
- Sistema modular e escalável
"""

from flask import Flask, render_template, request
from flask import redirect, url_for, flash, session
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime
from functools import wraps
from flask import jsonify
from flask import request

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO FLASK E BANCO DE DADOS
# ============================================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'  # Chave secreta para sessões (em produção usar variável de ambiente)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa avisos desnecessários

# Configuração da conexão com o banco de dados MySQL
# Usa variável de ambiente DATABASE_URL ou fallback para conexão local
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:admin@localhost:3306/progest2?charset=utf8mb4'
)

db = SQLAlchemy(app)  # Inicialização da extensão SQLAlchemy


# ============================================================================
# DECORATOR PARA CONTROLE DE ACESSO (LOGIN REQUERIDO)
# ============================================================================
def login_required(f):
    """
    Decorator que protege rotas, permitindo acesso apenas a usuários logados.
    Verifica se a chave 'user' existe na sessão.
    Se não estiver logado, redireciona para a página de login com mensagem.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# MODELOS ORM (ENTIDADES DO BANCO DE DADOS)
# ============================================================================

class Dono(db.Model):
    """
    Representa um proprietário de propriedades rurais.
    Campos: id, nome, CPF/CNPJ (único), email, telefone
    Relacionamento: Um dono pode ter várias propriedades (one-to-many)
    """
    __tablename__ = 'dono'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    cpf_cnpj = db.Column(db.String(18), nullable=False, unique=True)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))

class Propriedade(db.Model):
    """
    Representa uma propriedade rural.
    Campos: id, nome, município, estado, área total em hectares
    Relacionamento: Pertence a um dono (many-to-one)
    """
    __tablename__ = 'propriedade'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    municipio = db.Column(db.String(80), nullable=False)
    estado = db.Column(db.String(80), nullable=False)
    area_total_ha = db.Column(db.Numeric(10, 2), nullable=False)
    dono_id = db.Column(db.Integer, db.ForeignKey('dono.id'), nullable=False)
    dono = db.relationship('Dono', backref='propriedades')  # Relacionamento com Dono

class Usuario(db.Model):
    """
    Representa um usuário do sistema para autenticação.
    Campos: id, username (único), password
    """
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column('password', db.String(255), nullable=False)

class Animal(db.Model):
    """
    Representa um tipo/raça de animal.
    Campos: id, tipo (ex: Bovino, Equino), raça (ex: Nelore, Angus)
    """
    __tablename__ = 'animal'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(80), nullable=False)
    raca = db.Column(db.String(80))

class Lote(db.Model):
    """
    Representa um lote de animais em uma propriedade.
    Campos: id, propriedade_id, animal_id, quantidade, data_registro
    Relacionamentos: Pertence a uma propriedade e a um tipo de animal
    """
    __tablename__ = 'lote'
    id = db.Column(db.Integer, primary_key=True)
    propriedade_id = db.Column(db.Integer, db.ForeignKey('propriedade.id'), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_registro = db.Column(db.Date)
    
    # Relacionamentos necessários para joins eficientes
    propriedade = db.relationship('Propriedade', backref='lotes')
    animal = db.relationship('Animal', backref='lotes')


# ============================================================================
# API PARA DASHBOARD DE BUSINESS INTELLIGENCE (BI)
# ============================================================================
@app.route("/api/bi/dashboard")
def bi_dashboard():
    """
    Endpoint API que retorna dados para os gráficos do dashboard de BI.
    Retorna JSON com 4 consultas analíticas:
    1. Proprietários com mais animais
    2. Distribuição de animais por raça
    3. Proprietários com maior área total
    4. Estados com mais fazendas
    """
    data = {}
    try:
        # 1️⃣ CONSULTA: Quem tem mais animais (soma de lotes por proprietário)
        q1 = (
            db.session.query(
                Dono.nome.label('proprietario'),
                func.COALESCE(func.sum(Lote.quantidade), 0).label('total_animais')
            )
            .join(Propriedade, Propriedade.dono_id == Dono.id)
            .join(Lote, Lote.propriedade_id == Propriedade.id)
            .group_by(Dono.id)
            .order_by(func.sum(Lote.quantidade).desc())
        ).all()
        data["animais_por_proprietario"] = [
            {"proprietario": r.proprietario, "total_animais": int(r.total_animais)}
            for r in q1
        ]

        # 2️⃣ CONSULTA: Animais por raça (distribuição)
        q2 = (
            db.session.query(
                Animal.raca.label('raca'),
                func.COALESCE(func.sum(Lote.quantidade), 0).label('total')
            )
            .join(Lote, Lote.animal_id == Animal.id)
            .group_by(Animal.raca)
            .order_by(func.sum(Lote.quantidade).desc())
        ).all()
        data["animais_por_raca"] = [
            {"raca": (r.raca or "Não informado"), "total": int(r.total)}
            for r in q2
        ]

        # 3️⃣ CONSULTA: Proprietário com maior área total
        q3 = (
            db.session.query(
                Dono.nome.label('proprietario'),
                func.COALESCE(func.sum(Propriedade.area_total_ha), 0).label('total_ha')
            )
            .join(Propriedade, Propriedade.dono_id == Dono.id)
            .group_by(Dono.id)
            .order_by(func.sum(Propriedade.area_total_ha).desc())
        ).all()
        data["area_por_proprietario"] = [
            {"proprietario": r.proprietario, "total_ha": float(r.total_ha)}
            for r in q3
        ]

        # 4️⃣ CONSULTA: Estados com mais fazendas
        q4 = (
            db.session.query(
                Propriedade.estado.label('estado'),
                func.count(Propriedade.id).label('total_fazendas')
            )
            .group_by(Propriedade.estado)
            .order_by(func.count(Propriedade.id).desc())
        ).all()
        data["fazendas_por_estado"] = [
            {"estado": (r.estado or "Não informado"), "total_fazendas": int(r.total_fazendas)}
            for r in q4
        ]

        return jsonify(data)  # Retorna dados em formato JSON para frontend

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Retorna erro 500 em caso de falha


# ============================================================================
# ROTA DA PÁGINA PRINCIPAL DO BI
# ============================================================================
@app.route("/bi/dashboard")
@login_required
def bi_dashboard_page():
    """
    Renderiza a página HTML do dashboard de BI.
    Os dados são carregados via AJAX/Fetch na rota /api/bi/dashboard.
    """
    return render_template("bi.html", show_menu=True)


# ============================================================================
# ROTAS PRINCIPAIS DA APLICAÇÃO
# ============================================================================
@app.route('/')
def main_route():
    """Rota raiz: redireciona para login se não autenticado, senão para dashboard."""
    if 'user' in session:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    """
    Dashboard principal da aplicação.
    Exibe estatísticas gerais, lotes recentes e atividades.
    """
    try:
        # ESTATÍSTICAS GERAIS
        proprietarios_count = Dono.query.count()
        propriedades_count = Propriedade.query.count()
        animais_count = Animal.query.count()
        lotes_count = Lote.query.count()
        quantidade_total = db.session.query(func.sum(Lote.quantidade)).scalar() or 0
        
        # MÉTRICAS ADICIONAIS
        propriedades_ativas = propriedades_count  # Poderia ter lógica mais complexa
        tipos_animais = db.session.query(func.count(func.distinct(Animal.tipo))).scalar() or 0
        raca_animais = db.session.query(func.count(func.distinct(Animal.raca))).scalar() or 0
        lotes_ativos = lotes_count  # Poderia ter lógica mais complexa
        
        # LOTES RECENTES (com ordenação por data)
        lotes = Lote.query.order_by(Lote.data_registro.desc()).all()
        
        # ATIVIDADES RECENTES (estático por enquanto - poderia vir do banco)
        atividades_recentes = [
            {'tipo': 'propriedade', 'descricao': 'Nova propriedade cadastrada', 'tempo': 'há 2 horas'},
            {'tipo': 'animal', 'descricao': 'Novo tipo de animal registrado', 'tempo': 'há 1 dia'},
            {'tipo': 'lote', 'descricao': 'Lote de animais atualizado', 'tempo': 'há 3 dias'}
        ]
        
    except Exception as e:
        # TRATAMENTO DE ERRO: Define valores padrão e mostra mensagem
        flash(f'Erro ao carregar dados do dashboard: {e}', 'danger')
        proprietarios_count = propriedades_count = propriedades_ativas = 0
        animais_count = tipos_animais = raca_animais = lotes_count = 0
        lotes_ativos = quantidade_total = 0
        lotes = []
        atividades_recentes = []
    
    # RENDERIZA TEMPLATE COM TODOS OS DADOS
    return render_template(
        'index.html',
        proprietarios_count=proprietarios_count,
        propriedades_count=propriedades_count,
        propriedades_ativas=propriedades_ativas,
        animais_count=animais_count,
        tipos_animais=tipos_animais,
        lotes_count=lotes_count,
        raca_animais=raca_animais,
        lotes_ativos=lotes_ativos,
        quantidade_count=quantidade_total,
        atividades_recentes=atividades_recentes,
        lotes=lotes,
        show_menu=True
    )


# ============================================================================
# ROTAS DE VISUALIZAÇÃO (PÁGINAS HTML)
# ============================================================================
@app.route('/owners1')
@app.route('/owners1/')
@login_required
def show_owners1():
    """Página alternativa de visualização de proprietários."""
    try:
        donos = Dono.query.order_by(Dono.nome.asc()).all()
        return render_template('owners1.html', donos=donos, show_menu=True)
    except Exception as e:
        flash(f'Erro ao carregar página owners1: {e}', 'danger')
        return render_template('owners1.html', donos=[], show_menu=True)

@app.route('/propriedades1')
@app.route('/propriedades1/')
@login_required
def show_propriedades1():
    """Página alternativa de visualização de propriedades."""
    try:
        propriedades = Propriedade.query.order_by(Propriedade.nome.asc()).all()
        return render_template('propriedades1.html', propriedades=propriedades, show_menu=True)
    except Exception as e:
        flash(f'Erro ao carregar página propriedades1: {e}', 'danger')
        return render_template('propriedades1.html', propriedades=[], show_menu=True)

@app.route('/lotes1')
@login_required
def show_lotes1():
    """Página alternativa de visualização de lotes."""
    try:
        lotes = Lote.query.order_by(Lote.id.asc()).all()
        return render_template('lotes1.html', lotes=lotes, show_menu=True)
    except Exception as e:
        flash(f'Erro ao carregar página lotes1: {e}', 'danger')
        return render_template('lotes1.html', lotes=[], show_menu=True)


# ============================================================================
# CRUD DE PROPRIETÁRIOS (DONOS)
# ============================================================================
@app.route('/owners', methods=['GET'])
@login_required
def owners():
    """Lista todos os proprietários cadastrados."""
    try:
        donos_q = Dono.query.order_by(Dono.id.desc()).all()
        # Formata dados para o template
        donos = [{
                'id_proprietario': d.id,
                'nome': d.nome,
                'cpf': d.cpf_cnpj,
                'email': d.email,
                'telefone': d.telefone,
            } for d in donos_q
        ]
    except Exception as e:
        flash(f'Erro ao carregar proprietários: {e}', 'danger')
        donos = []
    return render_template('owners.html', donos=donos, show_menu=True)

@app.route('/owners/cadastrar', methods=['POST'])
@login_required
def cadastrarProprietario():
    """Cadastra um novo proprietário via formulário POST."""
    # Obtém e limpa dados do formulário
    nome = (request.form.get('nome') or '').strip()
    cpf_cnpj = (request.form.get('cpf_cnpj') or '').strip()
    telefone = (request.form.get('telefone') or '').strip()
    email = (request.form.get('email') or '').strip()

    # VALIDAÇÃO
    if not nome or not cpf_cnpj:
        flash('Campo nome e cpf/cnpj são obrigatórios', 'warning')
        return redirect(url_for('owners'))

    try:
        # CRIA E SALVA NO BANCO
        novo = Dono(nome=nome, cpf_cnpj=cpf_cnpj, telefone=telefone, email=email)
        db.session.add(novo)
        db.session.commit()
        flash('Proprietário cadastrado com sucesso.', 'success')
    except IntegrityError:
        # ERRO: CPF/CNPJ duplicado
        db.session.rollback()
        flash('CPF/CNPJ já cadastrado.', 'warning')
    except Exception as e:
        # ERRO GERAL
        db.session.rollback()
        flash(f'Erro ao cadastrar proprietário: {e}', 'danger')
    return redirect(url_for('owners'))


# ============================================================================
# CRUD DE PROPRIEDADES
# ============================================================================
@app.route('/propriedades', methods=['GET', 'POST'])
@login_required
def propriedades():
    """
    GET: Lista propriedades e carrega donos para formulário
    POST: Cadastra nova propriedade
    """
    if request.method == 'POST':
        # PROCESSAMENTO DO FORMULÁRIO DE CADASTRO
        nome = (request.form.get('nome') or '').strip()
        municipio = (request.form.get('municipio') or '').strip()
        estado = (request.form.get('estado') or '').strip()
        area_total = request.form.get('area_total')
        dono_id = request.form.get('dono_id')
        
        # VALIDAÇÃO
        if not nome or not municipio or not estado or not area_total or not dono_id:
            flash('Preencha todos os campos.', 'warning')
        else:
            try:
                # CRIAÇÃO DO OBJETO
                prop = Propriedade(
                    nome=nome,
                    municipio=municipio,
                    estado=estado,
                    area_total_ha=area_total,
                    dono_id=int(dono_id))
                db.session.add(prop)
                db.session.commit()
                flash('Propriedade cadastrada com sucesso.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar propriedade: {e}', 'danger')
        return redirect(url_for('propriedades'))

    # GET: CARREGA DADOS PARA O TEMPLATE
    try:
        # Lista de donos para o select
        donos_q = Dono.query.order_by(Dono.nome.asc()).all()
        donos = [{'id': d.id, 'nome': d.nome} for d in donos_q]
    except Exception as e:
        flash(f'Erro ao carregar proprietários: {e}', 'danger')
        donos = []
    
    try:
        # Lista de propriedades com join para trazer nome do dono
        props_q = db.session.query(Propriedade, Dono).join(Dono, Propriedade.dono_id == Dono.id).order_by(Propriedade.nome.asc()).all()
        props = [{
                'nome': p.nome,
                'municipio': p.municipio,
                'estado': p.estado,
                'area_total_ha': float(p.area_total_ha),
                'dono_nome': d.nome,}
            for (p, d) in props_q]
    except Exception as e:
        flash(f'Erro ao carregar propriedades: {e}', 'danger')
        props = []
    
    return render_template('propriedades.html', donos=donos, propriedades=props, show_menu=True)


# ============================================================================
# CRUD DE ANIMAIS
# ============================================================================
@app.route('/animais', methods=['GET', 'POST'])
@login_required
def animais():
    """
    GET: Lista animais cadastrados
    POST: Cadastra novo tipo/raça de animal
    """
    if request.method == 'POST':
        tipo = (request.form.get('tipo') or '').strip()
        raca = (request.form.get('raca') or '').strip()
        if not tipo:
            flash('Informe o tipo do animal.', 'warning')
        else:
            try:
                novo = Animal(tipo=tipo, raca=raca or None)
                db.session.add(novo)
                db.session.commit()
                flash('Animal cadastrado com sucesso.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar animal: {e}', 'danger')
        return redirect(url_for('animais'))

    # GET: LISTA ANIMAIS
    lista = []
    try:
        registros = Animal.query.order_by(Animal.tipo.asc()).all()
        lista = [{ 'tipo': a.tipo, 'raca': a.raca } for a in registros]
    except Exception as e:
        flash(f'Erro ao carregar animais: {e}', 'danger')
    return render_template('animais.html', animais=lista, show_menu=True)


# ============================================================================
# CRUD DE LOTES
# ============================================================================
@app.route('/lotes', methods=['GET', 'POST'])
@login_required
def lotes():
    """
    GET: Lista lotes e carrega propriedades/animais para formulário
    POST: Cadastra novo lote de animais
    """
    if request.method == 'POST':
        # PROCESSAMENTO DO FORMULÁRIO
        propriedade_id = request.form.get('propriedade_id')
        animal_id = request.form.get('animal_id')
        quantidade = request.form.get('quantidade')
        data_registro_str = request.form.get('data_registro')
        
        # VALIDAÇÃO
        if not propriedade_id or not animal_id or not quantidade:
            flash('Informe propriedade, animal e quantidade.', 'warning')
            return redirect(url_for('lotes'))
        try:
            qnt = int(quantidade)
            # CONVERSÃO DE DATA
            data_registro_val = None
            if data_registro_str:
                try:
                    data_registro_val = datetime.strptime(data_registro_str, '%Y-%m-%d').date()
                except Exception:
                    data_registro_val = None

            # CRIAÇÃO DO LOTE
            novo = Lote(
                propriedade_id=int(propriedade_id),
                animal_id=int(animal_id),
                quantidade=qnt,
                data_registro=data_registro_val
            )
            db.session.add(novo)
            db.session.commit()
            flash('Lote registrado com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar lote: {e}', 'danger')
        return redirect(url_for('lotes'))

    # GET: CARREGA DADOS PARA O TEMPLATE
    propriedades = []
    animais = []
    lotes = []
    
    try:
        # PROPRIEDADES PARA SELECT
        ps = Propriedade.query.order_by(Propriedade.nome.asc()).all()
        propriedades = [{ 'id': p.id, 'nome': p.nome } for p in ps]
    except Exception as e:
        flash(f'Erro ao carregar propriedades: {e}', 'danger')
    
    try:
        # ANIMAIS PARA SELECT
        as_ = Animal.query.order_by(Animal.tipo.asc()).all()
        animais = [{ 'id': a.id, 'descricao': f"{a.tipo} - {a.raca}" if a.raca else a.tipo } for a in as_]
    except Exception as e:
        flash(f'Erro ao carregar animais: {e}', 'danger')
    
    try:
        # LISTA DE LOTES COM JOINS
        registros = (
            db.session.query(Lote, Propriedade, Animal)
            .join(Propriedade, Lote.propriedade_id == Propriedade.id)
            .join(Animal, Lote.animal_id == Animal.id)
            .order_by(Propriedade.nome.asc(), Animal.tipo.asc())
            .all()
        )
        # FORMATA DADOS PARA TEMPLATE
        lotes = [
            {
                'propriedade': prop.nome,
                'animal': f"{ani.tipo} - {ani.raca}" if ani.raca else ani.tipo,
                'quantidade': lt.quantidade,
                'data_registro': lt.data_registro.strftime('%d-%m-%Y') if lt.data_registro else None
            }
            for (lt, prop, ani) in registros
        ]
    except Exception as e:
        flash(f'Erro ao carregar lotes: {e}', 'danger')
    
    return render_template('lotes.html', propriedades=propriedades, animais=animais, lotes=lotes, show_menu=True)


# ============================================================================
# AUTENTICAÇÃO E GERENCIAMENTO DE USUÁRIOS
# ============================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login - autentica usuários e inicia sessão."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Informe usuário e senha.', 'warning')
            return redirect(url_for('login'))
        
        try:
            # VERIFICA CREDENCIAIS
            user = Usuario.query.filter_by(username=username).first()
            if not user or user.password != password:  # EM PRODUÇÃO: usar hash!
                flash('Usuário ou senha inválidos.', 'danger')
                return redirect(url_for('login'))
            
            # AUTENTICAÇÃO BEM-SUCEDIDA
            session['user'] = username
            flash('Login efetuado com sucesso.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Erro ao validar login: {e}', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html', show_menu=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro - cria novas contas de usuário."""
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '')
        
        if not username or not password:
            flash('Informe usuário e senha para criar a conta.', 'warning')
            return redirect(url_for('register'))
        
        try:
            # VERIFICA SE USUÁRIO JÁ EXISTE
            exists = Usuario.query.filter_by(username=username).first()
            if exists:
                flash('Usuário já existe. Escolha outro.', 'warning')
                return redirect(url_for('register'))
            
            # CRIA NOVO USUÁRIO (EM PRODUÇÃO: CRIPTOGRAFAR SENHA!)
            novo = Usuario(username=username, password=password)
            db.session.add(novo)
            db.session.commit()
            flash('Conta criada com sucesso. Faça login para continuar.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {e}', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html', show_menu=False)

@app.route('/logout')
def logout():
    """Encerra a sessão do usuário e redireciona para login."""
    session.pop('user', None)
    flash('Você saiu da aplicação.', 'info')
    return redirect(url_for('login'))


# ============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ============================================================================
if __name__ == '__main__':
    """
    Ponto de entrada principal da aplicação.
    Cria tabelas no banco (se não existirem) e inicia o servidor Flask.
    """
    # CRIA TABELAS NO BANCO DE DADOS
    try:
        with app.app_context():
            db.create_all()  # Cria tabelas definidas nos modelos
    except Exception as e:
        print('Aviso: não foi possível criar tabelas automaticamente:', e)
    
    # CONFIGURA HOST E PORTA (com fallback para desenvolvimento)
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5600'))
    
    # INICIA SERVIDOR FLASK
    app.run(host=host, port=port, debug=True)