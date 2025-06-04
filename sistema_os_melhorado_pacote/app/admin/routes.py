"""
Rotas de administração.
Este módulo implementa as rotas relacionadas à administração do sistema.
"""
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from datetime import datetime
from zoneinfo import ZoneInfo

from app.admin import admin_bp
from app.admin.forms import (
    AdministradoraForm, CondominioForm, UserForm, RoleForm, 
    AreaForm, FornecedorForm, ApproveUserForm
)
from app.models import (
    User, Role, Condominio, Administradora, Area, Fornecedor, 
    UserCondominio, UserRole, ActivityLog, OrdemServico
)
from app.extensions import db
from app.utils.decorators import admin_required, log_activity
from app.utils.email import send_notification_email, send_welcome_email

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Rota para dashboard administrativo."""
    # Estatísticas gerais
    total_users = User.query.count()
    pending_users = User.query.filter_by(is_pending=True).count()
    total_condominios = Condominio.query.count()
    total_ordens = OrdemServico.query.count()
    ordens_abertas = OrdemServico.query.filter_by(status='Aberta').count()
    ordens_andamento = OrdemServico.query.filter_by(status='Em Andamento').count()
    ordens_concluidas = OrdemServico.query.filter_by(status='Concluída').count()
    
    # Usuários pendentes
    pending_users_list = User.query.filter_by(is_pending=True).all()
    
    # Atividades recentes
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/dashboard.html',
        title='Admin Dashboard',
        total_users=total_users,
        pending_users=pending_users,
        total_condominios=total_condominios,
        total_ordens=total_ordens,
        ordens_abertas=ordens_abertas,
        ordens_andamento=ordens_andamento,
        ordens_concluidas=ordens_concluidas,
        pending_users_list=pending_users_list,
        recent_activities=recent_activities
    )


# Rotas para gerenciamento de usuários
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Rota para listar usuários."""
    users = User.query.all()
    return render_template('admin/users.html', title='Usuários', users=users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('create_user')
def create_user():
    """Rota para criar novo usuário."""
    form = UserForm()
    
    # Carregar opções para os campos de seleção
    form.condominios.choices = [(c.id, c.nome) for c in Condominio.query.all()]
    form.roles.choices = [(r.id, r.name) for r in Role.query.all()]
    
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            is_admin=form.is_admin.data,
            is_pending=False,
            is_active=True
        )
        
        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Senha padrão temporária
            user.set_password('Temp@123')
        
        db.session.add(user)
        db.session.flush()  # Obter ID do usuário sem commit
        
        # Associar usuário aos condomínios selecionados
        for condominio_id in form.condominios.data:
            user_condominio = UserCondominio(
                user_id=user.id,
                condominio_id=condominio_id
            )
            db.session.add(user_condominio)
        
        # Associar usuário aos papéis selecionados
        for role_id in form.roles.data:
            user_role = UserRole(
                user_id=user.id,
                role_id=role_id
            )
            db.session.add(user_role)
        
        db.session.commit()
        
        # Enviar email de boas-vindas
        send_welcome_email(
            user_name=user.name,
            user_email=user.email
        )
        
        flash(f'Usuário {user.name} criado com sucesso!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', title='Novo Usuário', form=form)


@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('edit_user')
def edit_user(id):
    """Rota para editar usuário existente."""
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    # Carregar opções para os campos de seleção
    form.condominios.choices = [(c.id, c.nome) for c in Condominio.query.all()]
    form.roles.choices = [(r.id, r.name) for r in Role.query.all()]
    
    # Pré-selecionar valores atuais
    if request.method == 'GET':
        form.condominios.data = [c.id for c in user.condominios]
        form.roles.data = [r.id for r in user.roles]
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data.lower()
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Atualizar associações de condomínios
        UserCondominio.query.filter_by(user_id=user.id).delete()
        for condominio_id in form.condominios.data:
            user_condominio = UserCondominio(
                user_id=user.id,
                condominio_id=condominio_id
            )
            db.session.add(user_condominio)
        
        # Atualizar associações de papéis
        UserRole.query.filter_by(user_id=user.id).delete()
        for role_id in form.roles.data:
            user_role = UserRole(
                user_id=user.id,
                role_id=role_id
            )
            db.session.add(user_role)
        
        db.session.commit()
        flash(f'Usuário {user.name} atualizado com sucesso!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', title='Editar Usuário', form=form, user=user)


@admin_bp.route('/users/delete/<int:id>')
@login_required
@admin_required
@log_activity('delete_user')
def delete_user(id):
    """Rota para excluir usuário."""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário!', 'danger')
        return redirect(url_for('admin.users'))
    
    name = user.name
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuário {name} excluído com sucesso!', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/approve/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('approve_user')
def approve_user(id):
    """Rota para aprovar usuário pendente."""
    user = User.query.get_or_404(id)
    
    if not user.is_pending:
        flash('Este usuário já foi aprovado.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    form = ApproveUserForm()
    
    # Carregar opções para os campos de seleção
    form.roles.choices = [(r.id, r.name) for r in Role.query.all()]
    
    # Pré-selecionar papel padrão
    if request.method == 'GET':
        default_role = Role.query.filter_by(name='Usuario').first()
        if default_role:
            form.roles.data = [default_role.id]
    
    if form.validate_on_submit():
        user.is_pending = False
        
        # Associar usuário aos papéis selecionados
        for role_id in form.roles.data:
            user_role = UserRole(
                user_id=user.id,
                role_id=role_id
            )
            db.session.add(user_role)
        
        db.session.commit()
        
        # Enviar email de aprovação
        send_notification_email(
            subject='Sua conta foi aprovada',
            body=f"""
            <p>Olá {user.name},</p>
            <p>Sua conta no Sistema de OS foi aprovada e agora você pode acessar o sistema.</p>
            <p>Acesse com seu email: <strong>{user.email}</strong></p>
            <p>Atenciosamente,<br>Equipe do Sistema OS</p>
            """,
            to_email=user.email
        )
        
        flash(f'Usuário {user.name} aprovado com sucesso!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/approve_user.html', title='Aprovar Usuário', form=form, user=user)


# Rotas para gerenciamento de papéis (roles)
@admin_bp.route('/roles')
@login_required
@admin_required
def roles():
    """Rota para listar papéis."""
    roles = Role.query.all()
    return render_template('admin/roles.html', title='Papéis', roles=roles)


@admin_bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('create_role')
def create_role():
    """Rota para criar novo papel."""
    form = RoleForm()
    
    if form.validate_on_submit():
        role = Role(
            name=form.name.data,
            description=form.description.data,
            permissions=','.join(form.permissions.data)
        )
        
        db.session.add(role)
        db.session.commit()
        
        flash(f'Papel {role.name} criado com sucesso!', 'success')
        return redirect(url_for('admin.roles'))
    
    return render_template('admin/role_form.html', title='Novo Papel', form=form)


@admin_bp.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('edit_role')
def edit_role(id):
    """Rota para editar papel existente."""
    role = Role.query.get_or_404(id)
    form = RoleForm(obj=role)
    
    # Pré-selecionar permissões atuais
    if request.method == 'GET' and role.permissions:
        form.permissions.data = role.permissions.split(',')
    
    if form.validate_on_submit():
        role.name = form.name.data
        role.description = form.description.data
        role.permissions = ','.join(form.permissions.data)
        
        db.session.commit()
        flash(f'Papel {role.name} atualizado com sucesso!', 'success')
        return redirect(url_for('admin.roles'))
    
    return render_template('admin/role_form.html', title='Editar Papel', form=form, role=role)


@admin_bp.route('/roles/delete/<int:id>')
@login_required
@admin_required
@log_activity('delete_role')
def delete_role(id):
    """Rota para excluir papel."""
    role = Role.query.get_or_404(id)
    
    # Verificar se o papel está em uso
    if role.users:
        flash(f'Não é possível excluir o papel {role.name} pois está associado a usuários.', 'danger')
        return redirect(url_for('admin.roles'))
    
    name = role.name
    db.session.delete(role)
    db.session.commit()
    
    flash(f'Papel {name} excluído com sucesso!', 'success')
    return redirect(url_for('admin.roles'))


# Rotas para gerenciamento de administradoras
@admin_bp.route('/administradoras')
@login_required
@admin_required
def administradoras():
    """Rota para listar administradoras."""
    administradoras = Administradora.query.all()
    return render_template('admin/administradoras.html', title='Administradoras', administradoras=administradoras)


@admin_bp.route('/administradoras/new', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('create_administradora')
def create_administradora():
    """Rota para criar nova administradora."""
    form = AdministradoraForm()
    
    if form.validate_on_submit():
        administradora = Administradora(
            nome=form.nome.data,
            cnpj=form.cnpj.data,
            email=form.email.data,
            telefone=form.telefone.data,
            endereco=form.endereco.data,
            ativa=True
        )
        
        # Processar logo se enviado
        if form.logo.data:
            from app.utils.security import save_file
            filename = save_file(form.logo.data, directory=current_app.config['UPLOAD_FOLDER'])
            if filename:
                administradora.logo = filename
        
        db.session.add(administradora)
        db.session.commit()
        
        flash(f'Administradora {administradora.nome} criada com sucesso!', 'success')
        return redirect(url_for('admin.administradoras'))
    
    return render_template('admin/administradora_form.html', title='Nova Administradora', form=form)


@admin_bp.route('/administradoras/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('edit_administradora')
def edit_administradora(id):
    """Rota para editar administradora existente."""
    administradora = Administradora.query.get_or_404(id)
    form = AdministradoraForm(obj=administradora)
    
    if form.validate_on_submit():
        administradora.nome = form.nome.data
        administradora.cnpj = form.cnpj.data
        administradora.email = form.email.data
        administradora.telefone = form.telefone.data
        administradora.endereco = form.endereco.data
        administradora.ativa = form.ativa.data
        
        # Processar logo se enviado
        if form.logo.data:
            from app.utils.security import save_file
            filename = save_file(form.logo.data, directory=current_app.config['UPLOAD_FOLDER'])
            if filename:
                administradora.logo = filename
        
        db.session.commit()
        flash(f'Administradora {administradora.nome} atualizada com sucesso!', 'success')
        return redirect(url_for('admin.administradoras'))
    
    return render_template(
        'admin/administradora_form.html', 
        title='Editar Administradora', 
        form=form, 
        administradora=administradora
    )


@admin_bp.route('/administradoras/delete/<int:id>')
@login_required
@admin_required
@log_activity('delete_administradora')
def delete_administradora(id):
    """Rota para excluir administradora."""
    administradora = Administradora.query.get_or_404(id)
    
    # Verificar se a administradora tem condomínios
    if administradora.condominios.count() > 0:
        flash(
            f'Não é possível excluir a administradora {administradora.nome} pois possui condomínios associados.', 
            'danger'
        )
        return redirect(url_for('admin.administradoras'))
    
    nome = administradora.nome
    db.session.delete(administradora)
    db.session.commit()
    
    flash(f'Administradora {nome} excluída com sucesso!', 'success')
    return redirect(url_for('admin.administradoras'))


# Rotas para gerenciamento de condomínios
@admin_bp.route('/condominios')
@login_required
@admin_required
def condominios():
    """Rota para listar condomínios."""
    condominios = Condominio.query.all()
    return render_template('admin/condominios.html', title='Condomínios', condominios=condominios)


@admin_bp.route('/condominios/new', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('create_condominio')
def create_condominio():
    """Rota para criar novo condomínio."""
    form = CondominioForm()
    
    # Carregar administradoras para o select
    form.administradora_id.choices = [
        (a.id, a.nome) for a in Administradora.query.filter_by(ativa=True).all()
    ]
    
    if form.validate_on_submit():
        condominio = Condominio(
            nome=form.nome.data,
            endereco=form.endereco.data,
            cep=form.cep.data,
            cidade=form.cidade.data,
            estado=form.estado.data,
            telefone=form.telefone.data,
            email=form.email.data,
            administradora_id=form.administradora_id.data,
            ativo=True
        )
        
        db.session.add(condominio)
        db.session.commit()
        
        flash(f'Condomínio {condominio.nome} criado com sucesso!', 'success')
        return redirect(url_for('admin.condominios'))
    
    return render_template('admin/condominio_form.html', title='Novo Condomínio', form=form)


@admin_bp.route('/condominios/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('edit_condominio')
def edit_condominio(id):
    """Rota para editar condomínio existente."""
    condominio = Condominio.query.get_or_404(id)
    form = CondominioForm(obj=condominio)
    
    # Carregar administradoras para o select
    form.administradora_id.choices = [
        (a.id, a.nome) for a in Administradora.query.filter_by(ativa=True).all()
    ]
    
    if form.validate_on_submit():
        condominio.nome = form.nome.data
        condominio.endereco = form.endereco.data
        condominio.cep = form.cep.data
        condominio.cidade = form.cidade.data
        condominio.estado = form.estado.data
        condominio.telefone = form.telefone.data
        condominio.email = form.email.data
        condominio.administradora_id = form.administradora_id.data
        condominio.ativo = form.ativo.data
        
        db.session.commit()
        flash(f'Condomínio {condominio.nome} atualizado com sucesso!', 'success')
        return redirect(url_for('admin.condominios'))
    
    return render_template(
        'admin/condominio_form.html', 
        title='Editar Condomínio', 
        form=form, 
        condominio=condominio
    )


@admin_bp.route('/condominios/delete/<int:id>')
@login_required
@admin_required
@log_activity('delete_condominio')
def delete_condominio(id):
    """Rota para excluir condomínio."""
    condominio = Condominio.query.get_or_404(id)
    
    # Verificar se o condomínio tem ordens de serviço
    if condominio.ordens.count() > 0:
        flash(
            f'Não é possível excluir o condomínio {condominio.nome} pois possui ordens de serviço associadas.', 
            'danger'
        )
        return redirect(url_for('admin.condominios'))
    
    # Verificar se o condomínio tem usuários
    if condominio.users:
        flash(
            f'Não é possível excluir o condomínio {condominio.nome} pois possui usuários associados.', 
            'danger'
        )
        return redirect(url_for('admin.condominios'))
    
    nome = condominio.nome
    db.session.delete(condominio)
    db.session.commit()
    
    flash(f'Condomínio {nome} excluído com sucesso!', 'success')
    return redirect(url_for('admin.condominios'))


# Rotas para gerenciamento de áreas
@admin_bp.route('/areas')
@login_required
@admin_required
def areas():
    """Rota para listar áreas."""
    areas = Area.query.all()
    return render_template('admin/areas.html', title='Áreas', areas=areas)


@admin_bp.route('/areas/new', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('create_area')
def create_area():
    """Rota para criar nova área."""
    form = AreaForm()
    
    # Carregar condomínios para o select
    form.condominio_id.choices = [
        (c.id, c.nome) for c in Condominio.query.filter_by(ativo=True).all()
    ]
    
    if form.validate_on_submit():
        area = Area(
            nome=form.nome.data,
            descricao=form.descricao.data,
            condominio_id=form.condominio_id.data
        )
        
        db.session.add(area)
        db.session.commit()
        
        flash(f'Área {area.nome} criada com sucesso!', 'success')
        return redirect(url_for('admin.areas'))
    
    return render_template('admin/area_form.html', title='Nova Área', form=form)


@admin_bp.route('/areas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('edit_area')
def edit_area(id):
    """Rota para editar área existente."""
    area = Area.query.get_or_404(id)
    form = AreaForm(obj=area)
    
    # Carregar condomínios para o select
    form.condominio_id.choices = [
        (c.id, c.nome) for c in Condominio.query.filter_by(ativo=True).all()
    ]
    
    if form.validate_on_submit():
        area.nome = form.nome.data
        area.descricao = form.descricao.data
        area.condominio_id = form.condominio_id.data
        
        db.session.commit()
        flash(f'Área {area.nome} atualizada com sucesso!', 'success')
        return redirect(url_for('admin.areas'))
    
    return render_template('admin/area_form.html', title='Editar Área', form=form, area=area)


@admin_bp.route('/areas/delete/<int:id>')
@login_required
@admin_required
@log_activity('delete_area')
def delete_area(id):
    """Rota para excluir área."""
    area = Area.query.get_or_404(id)
    
    # Verificar se a área tem ordens de serviço
    if area.ordens.count() > 0:
        flash(
            f'Não é possível excluir a área {area.nome} pois possui ordens de serviço associadas.', 
            'danger'
        )
        return redirect(url_for('admin.areas'))
    
    nome = area.nome
    db.session.delete(area)
    db.session.commit()
    
    flash(f'Área {nome} excluída com sucesso!', 'success')
    return redirect(url_for('admin.areas'))


# Rotas para gerenciamento de fornecedores
@admin_bp.route('/fornecedores')
@login_required
@admin_required
def fornecedores():
    """Rota para listar fornecedores."""
    fornecedores = Fornecedor.query.all()
    return render_template('admin/fornecedores.html', title='Fornecedores', fornecedores=fornecedores)


@admin_bp.route('/fornecedores/new', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('create_fornecedor')
def create_fornecedor():
    """Rota para criar novo fornecedor."""
    form = FornecedorForm()
    
    if form.validate_on_submit():
        fornecedor = Fornecedor(
            nome=form.nome.data,
            cnpj_cpf=form.cnpj_cpf.data,
            email=form.email.data,
            telefone=form.telefone.data,
            endereco=form.endereco.data,
            tipo_servico=form.tipo_servico.data,
            observacoes=form.observacoes.data,
            ativo=True
        )
        
        db.session.add(fornecedor)
        db.session.commit()
        
        flash(f'Fornecedor {fornecedor.nome} criado com sucesso!', 'success')
        return redirect(url_for('admin.fornecedores'))
    
    return render_template('admin/fornecedor_form.html', title='Novo Fornecedor', form=form)


@admin_bp.route('/fornecedores/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
@log_activity('edit_fornecedor')
def edit_fornecedor(id):
    """Rota para editar fornecedor existente."""
    fornecedor = Fornecedor.query.get_or_404(id)
    form = FornecedorForm(obj=fornecedor)
    
    if form.validate_on_submit():
        fornecedor.nome = form.nome.data
        fornecedor.cnpj_cpf = form.cnpj_cpf.data
        fornecedor.email = form.email.data
        fornecedor.telefone = form.telefone.data
        fornecedor.endereco = form.endereco.data
        fornecedor.tipo_servico = form.tipo_servico.data
        fornecedor.observacoes = form.observacoes.data
        fornecedor.ativo = form.ativo.data
        
        db.session.commit()
        flash(f'Fornecedor {fornecedor.nome} atualizado com sucesso!', 'success')
        return redirect(url_for('admin.fornecedores'))
    
    return render_template(
        'admin/fornecedor_form.html', 
        title='Editar Fornecedor', 
        form=form, 
        fornecedor=fornecedor
    )


@admin_bp.route('/fornecedores/delete/<int:id>')
@login_required
@admin_required
@log_activity('delete_fornecedor')
def delete_fornecedor(id):
    """Rota para excluir fornecedor."""
    fornecedor = Fornecedor.query.get_or_404(id)
    
    # Verificar se o fornecedor tem ordens de serviço
    if fornecedor.ordens.count() > 0:
        flash(
            f'Não é possível excluir o fornecedor {fornecedor.nome} pois possui ordens de serviço associadas.', 
            'danger'
        )
        return redirect(url_for('admin.fornecedores'))
    
    nome = fornecedor.nome
    db.session.delete(fornecedor)
    db.session.commit()
    
    flash(f'Fornecedor {nome} excluído com sucesso!', 'success')
    return redirect(url_for('admin.fornecedores'))


# Rota para relatórios administrativos
@admin_bp.route('/relatorios')
@login_required
@admin_required
def relatorios():
    """Rota para relatórios administrativos."""
    return render_template('admin/relatorios.html', title='Relatórios Administrativos')


@admin_bp.route('/logs')
@login_required
@admin_required
def activity_logs():
    """Rota para visualizar logs de atividade."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return render_template('admin/logs.html', title='Logs de Atividade', logs=logs)
