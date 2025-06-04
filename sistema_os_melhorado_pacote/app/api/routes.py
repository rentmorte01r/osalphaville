"""
Rotas da API.
Este módulo implementa as rotas da API REST para acesso programático ao sistema.
"""
from flask import jsonify, request, current_app
from flask_login import current_user, login_required
from datetime import datetime
from zoneinfo import ZoneInfo

from app.api import api_bp
from app.models import OrdemServico, Condominio, User, Area, Fornecedor
from app.extensions import db
from app.utils.decorators import permission_required

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


@api_bp.route('/ordens', methods=['GET'])
@login_required
def get_ordens():
    """Endpoint para obter ordens de serviço."""
    # Obter parâmetros de filtro
    condominio_id = request.args.get('condominio_id', type=int)
    status = request.args.get('status')
    prioridade = request.args.get('prioridade')
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    
    # Construir query base
    query = OrdemServico.query
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros
    if condominio_id:
        query = query.filter_by(condominio_id=condominio_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if prioridade:
        query = query.filter_by(prioridade=prioridade)
    
    if data_inicial:
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').replace(tzinfo=FORTALEZA_TZ)
        query = query.filter(OrdemServico.data_criacao >= data_inicial_obj)
    
    if data_final:
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=FORTALEZA_TZ)
        query = query.filter(OrdemServico.data_criacao <= data_final_obj)
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limitar tamanho da página
    if per_page > 100:
        per_page = 100
    
    # Executar query com paginação
    ordens_paginadas = query.order_by(OrdemServico.data_criacao.desc()).paginate(page=page, per_page=per_page)
    
    # Formatar resultados
    ordens = []
    for ordem in ordens_paginadas.items:
        ordens.append({
            'id': ordem.id,
            'numero': ordem.numero,
            'titulo': ordem.titulo,
            'descricao': ordem.descricao,
            'status': ordem.status,
            'prioridade': ordem.prioridade,
            'tipo': ordem.tipo,
            'condominio': ordem.condominio.nome,
            'data_criacao': ordem.data_criacao.isoformat() if ordem.data_criacao else None,
            'data_conclusao': ordem.data_conclusao.isoformat() if ordem.data_conclusao else None
        })
    
    return jsonify({
        'ordens': ordens,
        'total': ordens_paginadas.total,
        'pages': ordens_paginadas.pages,
        'page': page,
        'per_page': per_page
    })


@api_bp.route('/ordens/<int:id>', methods=['GET'])
@login_required
def get_ordem(id):
    """Endpoint para obter detalhes de uma ordem de serviço."""
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Formatar comentários
    comentarios = []
    for comentario in ordem.comentarios:
        comentarios.append({
            'id': comentario.id,
            'texto': comentario.texto,
            'usuario': comentario.usuario.name,
            'data': comentario.data_criacao.isoformat()
        })
    
    # Formatar logs de status
    logs = []
    for log in ordem.status_logs:
        logs.append({
            'id': log.id,
            'status_anterior': log.status_anterior,
            'status_novo': log.status_novo,
            'usuario': log.usuario.name,
            'data': log.data_mudanca.isoformat(),
            'observacao': log.observacao
        })
    
    # Formatar arquivos
    arquivos = []
    for arquivo in ordem.arquivos:
        arquivos.append({
            'id': arquivo.id,
            'nome': arquivo.nome,
            'tipo': arquivo.tipo,
            'data_upload': arquivo.data_upload.isoformat()
        })
    
    # Formatar resultado
    result = {
        'id': ordem.id,
        'numero': ordem.numero,
        'titulo': ordem.titulo,
        'descricao': ordem.descricao,
        'status': ordem.status,
        'prioridade': ordem.prioridade,
        'tipo': ordem.tipo,
        'observacoes': ordem.observacoes,
        'valor_estimado': float(ordem.valor_estimado) if ordem.valor_estimado else None,
        'valor_final': float(ordem.valor_final) if ordem.valor_final else None,
        'condominio': {
            'id': ordem.condominio.id,
            'nome': ordem.condominio.nome
        },
        'area': {
            'id': ordem.area.id,
            'nome': ordem.area.nome
        } if ordem.area else None,
        'fornecedor': {
            'id': ordem.fornecedor.id,
            'nome': ordem.fornecedor.nome
        } if ordem.fornecedor else None,
        'responsavel': {
            'id': ordem.user.id,
            'nome': ordem.user.name
        } if ordem.user else None,
        'criador': {
            'id': ordem.criador.id,
            'nome': ordem.criador.name
        },
        'data_criacao': ordem.data_criacao.isoformat() if ordem.data_criacao else None,
        'data_inicio': ordem.data_inicio.isoformat() if ordem.data_inicio else None,
        'data_previsao': ordem.data_previsao.isoformat() if ordem.data_previsao else None,
        'data_conclusao': ordem.data_conclusao.isoformat() if ordem.data_conclusao else None,
        'comentarios': comentarios,
        'logs': logs,
        'arquivos': arquivos
    }
    
    return jsonify(result)


@api_bp.route('/condominios', methods=['GET'])
@login_required
def get_condominios():
    """Endpoint para obter condomínios."""
    # Construir query base
    if current_user.is_admin:
        condominios = Condominio.query.filter_by(ativo=True).all()
    else:
        condominios = current_user.condominios
    
    # Formatar resultados
    result = []
    for condominio in condominios:
        result.append({
            'id': condominio.id,
            'nome': condominio.nome,
            'administradora': condominio.administradora.nome
        })
    
    return jsonify(result)


@api_bp.route('/areas/<int:condominio_id>', methods=['GET'])
@login_required
def get_areas(condominio_id):
    """Endpoint para obter áreas de um condomínio."""
    # Verificar se o usuário tem acesso ao condomínio
    if not current_user.is_admin and condominio_id not in [c.id for c in current_user.condominios]:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Obter áreas
    areas = Area.query.filter_by(condominio_id=condominio_id).all()
    
    # Formatar resultados
    result = []
    for area in areas:
        result.append({
            'id': area.id,
            'nome': area.nome,
            'descricao': area.descricao
        })
    
    return jsonify(result)


@api_bp.route('/fornecedores', methods=['GET'])
@login_required
def get_fornecedores():
    """Endpoint para obter fornecedores."""
    # Obter fornecedores
    fornecedores = Fornecedor.query.filter_by(ativo=True).all()
    
    # Formatar resultados
    result = []
    for fornecedor in fornecedores:
        result.append({
            'id': fornecedor.id,
            'nome': fornecedor.nome,
            'tipo_servico': fornecedor.tipo_servico
        })
    
    return jsonify(result)


@api_bp.route('/estatisticas', methods=['GET'])
@login_required
def get_estatisticas():
    """Endpoint para obter estatísticas gerais."""
    # Obter parâmetros de filtro
    condominio_id = request.args.get('condominio_id', type=int)
    
    # Construir query base
    query = OrdemServico.query
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtro de condomínio se especificado
    if condominio_id:
        query = query.filter_by(condominio_id=condominio_id)
    
    # Calcular estatísticas
    total_ordens = query.count()
    ordens_abertas = query.filter_by(status='Aberta').count()
    ordens_andamento = query.filter_by(status='Em Andamento').count()
    ordens_concluidas = query.filter_by(status='Concluída').count()
    
    # Estatísticas por prioridade
    alta_prioridade = query.filter_by(prioridade='Alta').count()
    normal_prioridade = query.filter_by(prioridade='Normal').count()
    baixa_prioridade = query.filter_by(prioridade='Baixa').count()
    
    return jsonify({
        'total_ordens': total_ordens,
        'por_status': {
            'abertas': ordens_abertas,
            'andamento': ordens_andamento,
            'concluidas': ordens_concluidas
        },
        'por_prioridade': {
            'alta': alta_prioridade,
            'normal': normal_prioridade,
            'baixa': baixa_prioridade
        }
    })


@api_bp.route('/ordens', methods=['POST'])
@login_required
@permission_required('create_order')
def create_ordem():
    """Endpoint para criar uma nova ordem de serviço."""
    # Obter dados do request
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    # Validar campos obrigatórios
    required_fields = ['titulo', 'descricao', 'prioridade', 'condominio_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo obrigatório ausente: {field}'}), 400
    
    # Verificar se o usuário tem acesso ao condomínio
    condominio_id = data['condominio_id']
    if not current_user.is_admin and condominio_id not in [c.id for c in current_user.condominios]:
        return jsonify({'error': 'Acesso negado ao condomínio especificado'}), 403
    
    # Criar nova ordem
    ordem = OrdemServico(
        titulo=data['titulo'],
        descricao=data['descricao'],
        prioridade=data['prioridade'],
        tipo=data.get('tipo', 'Manutenção'),
        condominio_id=condominio_id,
        criador_id=current_user.id,
        status='Aberta',
        observacoes=data.get('observacoes')
    )
    
    # Campos opcionais
    if 'area_id' in data and data['area_id']:
        ordem.area_id = data['area_id']
    
    if 'fornecedor_id' in data and data['fornecedor_id']:
        ordem.fornecedor_id = data['fornecedor_id']
    
    if 'valor_estimado' in data and data['valor_estimado']:
        ordem.valor_estimado = data['valor_estimado']
    
    if 'data_previsao' in data and data['data_previsao']:
        ordem.data_previsao = datetime.fromisoformat(data['data_previsao'])
    
    # Salvar ordem
    db.session.add(ordem)
    
    # Registrar log de status inicial
    from app.models import OrdemStatusLog
    log = OrdemStatusLog(
        ordem_id=ordem.id,
        status_anterior='',
        status_novo='Aberta',
        usuario_id=current_user.id,
        observacao='Ordem criada via API'
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Ordem criada com sucesso',
        'id': ordem.id,
        'numero': ordem.numero
    }), 201


@api_bp.route('/ordens/<int:id>/status', methods=['PUT'])
@login_required
@permission_required('edit_order')
def update_ordem_status(id):
    """Endpoint para atualizar o status de uma ordem de serviço."""
    # Obter ordem
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Obter dados do request
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'error': 'Status não especificado'}), 400
    
    # Validar status
    novo_status = data['status']
    status_validos = ['Aberta', 'Em Andamento', 'Aguardando Aprovação', 'Aguardando Material', 'Concluída', 'Cancelada']
    
    if novo_status not in status_validos:
        return jsonify({'error': 'Status inválido'}), 400
    
    # Atualizar status
    if novo_status != ordem.status:
        observacao = data.get('observacao', '')
        ordem.atualizar_status(novo_status, current_user.id, observacao)
        
        # Se o status for "Concluída", registrar data de conclusão
        if novo_status == 'Concluída' and not ordem.data_conclusao:
            ordem.data_conclusao = datetime.now(FORTALEZA_TZ)
        
        db.session.commit()
    
    return jsonify({
        'message': 'Status atualizado com sucesso',
        'status': novo_status
    })


@api_bp.route('/ordens/<int:id>/comentarios', methods=['POST'])
@login_required
def add_comentario(id):
    """Endpoint para adicionar um comentário a uma ordem de serviço."""
    # Obter ordem
    ordem = OrdemServico.query.get_or_404(id)
    
    # Verificar se o usuário tem acesso ao condomínio da ordem
    if not current_user.is_admin and ordem.condominio_id not in [c.id for c in current_user.condominios]:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Obter dados do request
    data = request.get_json()
    
    if not data or 'texto' not in data:
        return jsonify({'error': 'Texto do comentário não especificado'}), 400
    
    # Adicionar comentário
    from app.models import OrdemComentario
    comentario = OrdemComentario(
        ordem_id=ordem.id,
        usuario_id=current_user.id,
        texto=data['texto']
    )
    
    db.session.add(comentario)
    db.session.commit()
    
    return jsonify({
        'message': 'Comentário adicionado com sucesso',
        'id': comentario.id
    }), 201
