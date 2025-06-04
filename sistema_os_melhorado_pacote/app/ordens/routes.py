"""
Rotas de ordens de serviço.
Este módulo implementa as rotas relacionadas às ordens de serviço.
"""
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from app.ordens import ordens_bp
from app.ordens.forms import OrdemForm, OrdemEditForm, OrdemComentarioForm, OrdemFiltroForm
from app.models import (
    OrdemServico, OrdemStatusLog, OrdemComentario, OrdemArquivo,
    Condominio, Area, Fornecedor, User
)
from app.extensions import db
from app.utils.decorators import permission_required, log_activity
from app.utils.email import send_ordem_status_update_email
from app.utils.security import save_file

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


@ordens_bp.route('/painel')
@login_required
def painel():
    """Rota para painel principal de ordens de serviço."""
    # Estatísticas para o usuário atual
    condominios = current_user.condominios
    
    # Filtrar ordens pelos condomínios do usuário
    query = OrdemServico.query.filter(OrdemServico.condominio_id.in_([c.id for c in condominios]))
    
    total_ordens = query.count()
    ordens_abertas = query.filter_by(status='Aberta').count()
    ordens_andamento = query.filter_by(status='Em Andamento').count()
    ordens_concluidas = query.filter_by(status='Concluída').count()
    
    # Ordens recentes
    ordens_recentes = query.order_by(OrdemServico.data_criacao.desc()).limit(5).all()
    
    return render_template(
        'ordens/painel.html',
        title='Painel',
        total_ordens=total_ordens,
        ordens_abertas=ordens_abertas,
        ordens_andamento=ordens_andamento,
        ordens_concluidas=ordens_concluidas,
        ordens_recentes=ordens_recentes
    )


@ordens_bp.route('/')
@login_required
def listar():
    """Rota para listar ordens de serviço."""
    form = OrdemFiltroForm()
    
    # Preencher opções de condomínios
    form.condominio_id.choices = [(0, 'Todos')] + [
        (c.id, c.nome) for c in current_user.condominios
    ]
    
    # Obter parâmetros de filtro
    condominio_id = request.args.get('condominio_id', type=int)
    status = request.args.get('status', 'Todos')
    prioridade = request.args.get('prioridade', 'Todas')
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    
    # Construir query base
    query = OrdemServico.query
    
    # Filtrar por condomínios do usuário
    if current_user.is_admin:
        # Administradores podem ver todas as ordens
        pass
    else:
        # Usuários normais só veem ordens dos seus condomínios
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros
    if condominio_id and condominio_id > 0:
        query = query.filter_by(condominio_id=condominio_id)
    
    if status != 'Todos':
        query = query.filter_by(status=status)
    
    if prioridade != 'Todas':
        query = query.filter_by(prioridade=prioridade)
    
    if data_inicial:
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').replace(tzinfo=FORTALEZA_TZ)
        query = query.filter(OrdemServico.data_criacao >= data_inicial_obj)
    
    if data_final:
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=FORTALEZA_TZ)
        query = query.filter(OrdemServico.data_criacao <= data_final_obj)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    ordens = query.order_by(OrdemServico.data_criacao.desc()).paginate(page=page, per_page=per_page)
    
    return render_template(
        'ordens/listar.html',
        title='Ordens de Serviço',
        ordens=ordens,
        form=form,
        condominio_id=condominio_id,
        status=status,
        prioridade=prioridade,
        data_inicial=data_inicial,
        data_final=data_final
    )


@ordens_bp.route('/concluidas')
@login_required
def concluidas():
    """Rota para listar ordens de serviço concluídas."""
    form = OrdemFiltroForm()
    
    # Preencher opções de condomínios
    form.condominio_id.choices = [(0, 'Todos')] + [
        (c.id, c.nome) for c in current_user.condominios
    ]
    
    # Obter parâmetros de filtro
    condominio_id = request.args.get('condominio_id', type=int)
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    
    # Construir query base
    query = OrdemServico.query.filter_by(status='Concluída')
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros
    if condominio_id and condominio_id > 0:
        query = query.filter_by(condominio_id=condominio_id)
    
    if data_inicial:
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').replace(tzinfo=FORTALEZA_TZ)
        query = query.filter(OrdemServico.data_conclusao >= data_inicial_obj)
    
    if data_final:
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=FORTALEZA_TZ)
        query = query.filter(OrdemServico.data_conclusao <= data_final_obj)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    ordens = query.order_by(OrdemServico.data_conclusao.desc()).paginate(page=page, per_page=per_page)
    
    return render_template(
        'ordens/concluidas.html',
        title='Ordens Concluídas',
        ordens=ordens,
        form=form,
        condominio_id=condominio_id,
        data_inicial=data_inicial,
        data_final=data_final
    )


@ordens_bp.route('/nova', methods=['GET', 'POST'])
@login_required
@permission_required('create_order')
@log_activity('create_ordem')
def nova():
    """Rota para criar nova ordem de serviço."""
    form = OrdemForm()
    
    # Preencher opções de condomínios
    form.condominio_id.choices = [
        (c.id, c.nome) for c in current_user.condominios
    ]
    
    # Preencher opções de áreas (será atualizado via AJAX)
    if form.condominio_id.data:
        areas = Area.query.filter_by(condominio_id=form.condominio_id.data).all()
        form.area_id.choices = [(0, 'Selecione...')] + [(a.id, a.nome) for a in areas]
    else:
        form.area_id.choices = [(0, 'Selecione...')]
    
    # Preencher opções de fornecedores
    form.fornecedor_id.choices = [(0, 'Selecione...')] + [
        (f.id, f.nome) for f in Fornecedor.query.filter_by(ativo=True).all()
    ]
    
    if form.validate_on_submit():
        ordem = OrdemServico(
            titulo=form.titulo.data,
            descricao=form.descricao.data,
            prioridade=form.prioridade.data,
            tipo=form.tipo.data,
            condominio_id=form.condominio_id.data,
            criador_id=current_user.id,
            status='Aberta'
        )
        
        # Campos opcionais
        if form.area_id.data and form.area_id.data > 0:
            ordem.area_id = form.area_id.data
        
        if form.fornecedor_id.data and form.fornecedor_id.data > 0:
            ordem.fornecedor_id = form.fornecedor_id.data
        
        if form.observacoes.data:
            ordem.observacoes = form.observacoes.data
        
        if form.valor_estimado.data:
            ordem.valor_estimado = form.valor_estimado.data
        
        if form.data_previsao.data:
            ordem.data_previsao = form.data_previsao.data.replace(tzinfo=FORTALEZA_TZ)
        
        # Processar arquivos
        if form.foto_inicial.data:
            filename = save_file(form.foto_inicial.data)
            if filename:
                ordem.foto_inicial = filename
                
                # Registrar arquivo
                ordem.arquivos.append(OrdemArquivo(
                    nome=form.foto_inicial.data.filename,
                    caminho=filename,
                    tipo='foto_inicial',
                    usuario_id=current_user.id
                ))
        
        if form.cotacao.data:
            filename = save_file(form.cotacao.data)
            if filename:
                ordem.cotacao = filename
                
                # Registrar arquivo
                ordem.arquivos.append(OrdemArquivo(
                    nome=form.cotacao.data.filename,
                    caminho=filename,
                    tipo='cotacao',
                    usuario_id=current_user.id
                ))
        
        # Salvar ordem
        db.session.add(ordem)
        
        # Registrar log de status inicial
        log = OrdemStatusLog(
            ordem_id=ordem.id,
            status_anterior='',
            status_novo='Aberta',
            usuario_id=current_user.id,
            observacao='Ordem criada'
        )
        db.session.add(log)
        
        db.session.commit()
        
        flash(f'Ordem de serviço #{ordem.numero} criada com sucesso!', 'success')
        return redirect(url_for('ordens.detalhe', id=ordem.id))
    
    return render_template('ordens/form.html', title='Nova Ordem de Serviço', form=form)


@ordens_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_order')
@log_activity('edit_ordem')
def editar(id):
    """Rota para editar ordem de serviço."""
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        flash('Você não tem permissão para editar esta ordem de serviço.', 'danger')
        return redirect(url_for('ordens.listar'))
    
    form = OrdemEditForm(obj=ordem)
    
    # Preencher opções de condomínios
    form.condominio_id.choices = [
        (c.id, c.nome) for c in current_user.condominios
    ]
    
    # Preencher opções de áreas
    areas = Area.query.filter_by(condominio_id=ordem.condominio_id).all()
    form.area_id.choices = [(0, 'Selecione...')] + [(a.id, a.nome) for a in areas]
    
    # Preencher opções de fornecedores
    form.fornecedor_id.choices = [(0, 'Selecione...')] + [
        (f.id, f.nome) for f in Fornecedor.query.filter_by(ativo=True).all()
    ]
    
    # Preencher opções de usuários para atribuição
    usuarios = User.query.join(UserCondominio).filter(
        UserCondominio.condominio_id == ordem.condominio_id,
        User.is_active == True,
        User.is_pending == False
    ).all()
    form.user_id.choices = [(0, 'Selecione...')] + [(u.id, u.name) for u in usuarios]
    
    if form.validate_on_submit():
        # Verificar se houve mudança de status
        status_anterior = ordem.status
        
        # Atualizar campos básicos
        ordem.titulo = form.titulo.data
        ordem.descricao = form.descricao.data
        ordem.prioridade = form.prioridade.data
        ordem.tipo = form.tipo.data
        ordem.condominio_id = form.condominio_id.data
        ordem.observacoes = form.observacoes.data
        
        # Campos opcionais
        if form.area_id.data and form.area_id.data > 0:
            ordem.area_id = form.area_id.data
        else:
            ordem.area_id = None
        
        if form.fornecedor_id.data and form.fornecedor_id.data > 0:
            ordem.fornecedor_id = form.fornecedor_id.data
        else:
            ordem.fornecedor_id = None
        
        if form.user_id.data and form.user_id.data > 0:
            ordem.user_id = form.user_id.data
        else:
            ordem.user_id = None
        
        if form.valor_estimado.data:
            ordem.valor_estimado = form.valor_estimado.data
        
        if form.valor_final.data:
            ordem.valor_final = form.valor_final.data
        
        if form.data_previsao.data:
            ordem.data_previsao = form.data_previsao.data.replace(tzinfo=FORTALEZA_TZ)
        
        # Processar arquivos
        if form.foto_inicial.data:
            filename = save_file(form.foto_inicial.data)
            if filename:
                ordem.foto_inicial = filename
                
                # Registrar arquivo
                ordem.arquivos.append(OrdemArquivo(
                    nome=form.foto_inicial.data.filename,
                    caminho=filename,
                    tipo='foto_inicial',
                    usuario_id=current_user.id
                ))
        
        if form.foto_andamento.data:
            filename = save_file(form.foto_andamento.data)
            if filename:
                ordem.foto_andamento = filename
                
                # Registrar arquivo
                ordem.arquivos.append(OrdemArquivo(
                    nome=form.foto_andamento.data.filename,
                    caminho=filename,
                    tipo='foto_andamento',
                    usuario_id=current_user.id
                ))
        
        if form.foto_final.data:
            filename = save_file(form.foto_final.data)
            if filename:
                ordem.foto_final = filename
                
                # Registrar arquivo
                ordem.arquivos.append(OrdemArquivo(
                    nome=form.foto_final.data.filename,
                    caminho=filename,
                    tipo='foto_final',
                    usuario_id=current_user.id
                ))
        
        if form.cotacao.data:
            filename = save_file(form.cotacao.data)
            if filename:
                ordem.cotacao = filename
                
                # Registrar arquivo
                ordem.arquivos.append(OrdemArquivo(
                    nome=form.cotacao.data.filename,
                    caminho=filename,
                    tipo='cotacao',
                    usuario_id=current_user.id
                ))
        
        # Atualizar status
        if form.status.data != status_anterior:
            ordem.atualizar_status(form.status.data, current_user.id, form.observacoes.data)
            
            # Se o status for "Concluída", registrar data de conclusão
            if form.status.data == 'Concluída' and not ordem.data_conclusao:
                ordem.data_conclusao = datetime.now(FORTALEZA_TZ)
            
            # Enviar email de notificação
            if ordem.user_id:
                send_ordem_status_update_email(ordem, ordem.user.name, ordem.user.email)
        
        db.session.commit()
        
        flash(f'Ordem de serviço #{ordem.numero} atualizada com sucesso!', 'success')
        return redirect(url_for('ordens.detalhe', id=ordem.id))
    
    return render_template('ordens/form_edit.html', title='Editar Ordem de Serviço', form=form, ordem=ordem)


@ordens_bp.route('/detalhe/<int:id>', methods=['GET', 'POST'])
@login_required
def detalhe(id):
    """Rota para visualizar detalhes de uma ordem de serviço."""
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        flash('Você não tem permissão para visualizar esta ordem de serviço.', 'danger')
        return redirect(url_for('ordens.listar'))
    
    # Formulário para comentários
    form = OrdemComentarioForm()
    
    if form.validate_on_submit():
        comentario = OrdemComentario(
            ordem_id=ordem.id,
            usuario_id=current_user.id,
            texto=form.texto.data
        )
        
        db.session.add(comentario)
        db.session.commit()
        
        flash('Comentário adicionado com sucesso!', 'success')
        return redirect(url_for('ordens.detalhe', id=ordem.id))
    
    return render_template(
        'ordens/detalhe.html',
        title=f'Ordem #{ordem.numero}',
        ordem=ordem,
        form=form
    )


@ordens_bp.route('/atualizar-status/<int:id>', methods=['POST'])
@login_required
@permission_required('edit_order')
@log_activity('update_status_ordem')
def atualizar_status(id):
    """Rota para atualizar status de uma ordem de serviço."""
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        flash('Você não tem permissão para atualizar esta ordem de serviço.', 'danger')
        return redirect(url_for('ordens.listar'))
    
    novo_status = request.form.get('status')
    observacao = request.form.get('observacao', '')
    
    if novo_status and novo_status != ordem.status:
        ordem.atualizar_status(novo_status, current_user.id, observacao)
        
        # Se o status for "Concluída", registrar data de conclusão
        if novo_status == 'Concluída' and not ordem.data_conclusao:
            ordem.data_conclusao = datetime.now(FORTALEZA_TZ)
        
        db.session.commit()
        
        # Enviar email de notificação
        if ordem.user_id:
            send_ordem_status_update_email(ordem, ordem.user.name, ordem.user.email)
        
        flash(f'Status da ordem #{ordem.numero} atualizado para {novo_status}!', 'success')
    
    return redirect(url_for('ordens.detalhe', id=ordem.id))


@ordens_bp.route('/excluir/<int:id>')
@login_required
@permission_required('delete_order')
@log_activity('delete_ordem')
def excluir(id):
    """Rota para excluir uma ordem de serviço."""
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        flash('Você não tem permissão para excluir esta ordem de serviço.', 'danger')
        return redirect(url_for('ordens.listar'))
    
    numero = ordem.numero
    db.session.delete(ordem)
    db.session.commit()
    
    flash(f'Ordem de serviço #{numero} excluída com sucesso!', 'success')
    return redirect(url_for('ordens.listar'))


@ordens_bp.route('/areas-por-condominio/<int:condominio_id>')
@login_required
def areas_por_condominio(condominio_id):
    """Rota para obter áreas de um condomínio (AJAX)."""
    areas = Area.query.filter_by(condominio_id=condominio_id).all()
    return jsonify([{'id': a.id, 'nome': a.nome} for a in areas])


@ordens_bp.route('/usuarios-por-condominio/<int:condominio_id>')
@login_required
def usuarios_por_condominio(condominio_id):
    """Rota para obter usuários de um condomínio (AJAX)."""
    usuarios = User.query.join(UserCondominio).filter(
        UserCondominio.condominio_id == condominio_id,
        User.is_active == True,
        User.is_pending == False
    ).all()
    return jsonify([{'id': u.id, 'nome': u.name} for u in usuarios])
