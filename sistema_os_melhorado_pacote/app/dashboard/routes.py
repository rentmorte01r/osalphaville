"""
Rotas de dashboard.
Este módulo implementa as rotas relacionadas ao dashboard e visualizações estatísticas.
"""
from flask import render_template, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import func, and_, extract

from app.dashboard import dashboard_bp
from app.models import OrdemServico, Condominio, User
from app.extensions import db
from app.utils.decorators import cache_control

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


@dashboard_bp.route('/')
@login_required
@cache_control(max_age=300)  # Cache por 5 minutos
def index():
    """Rota principal do dashboard."""
    # Obter parâmetros de filtro
    condominio_id = request.args.get('condominio_id', type=int)
    periodo = request.args.get('periodo', 'mes')  # dia, semana, mes, ano
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    
    # Preparar filtros para condominios
    condominios = current_user.condominios
    if current_user.is_admin:
        condominios = Condominio.query.filter_by(ativo=True).all()
    
    # Estatísticas gerais
    stats = obter_estatisticas_gerais(condominio_id)
    
    return render_template(
        'dashboard/index.html',
        title='Dashboard',
        stats=stats,
        condominios=condominios,
        condominio_id=condominio_id,
        periodo=periodo,
        data_inicial=data_inicial,
        data_final=data_final
    )


@dashboard_bp.route('/data')
@login_required
def dashboard_data():
    """Rota para obter dados do dashboard via AJAX."""
    # Obter parâmetros de filtro
    condominio_id = request.args.get('condominio_id', type=int)
    periodo = request.args.get('periodo', 'mes')  # dia, semana, mes, ano
    data_inicial_str = request.args.get('data_inicial')
    data_final_str = request.args.get('data_final')
    
    # Converter strings de data para objetos datetime
    data_inicial = None
    data_final = None
    
    if data_inicial_str:
        data_inicial = datetime.strptime(data_inicial_str, '%Y-%m-%d').replace(tzinfo=FORTALEZA_TZ)
    
    if data_final_str:
        data_final = datetime.strptime(data_final_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=FORTALEZA_TZ)
    
    # Definir período padrão se não especificado
    if not data_inicial and not data_final:
        hoje = datetime.now(FORTALEZA_TZ)
        
        if periodo == 'dia':
            data_inicial = hoje - timedelta(days=7)
            data_final = hoje
        elif periodo == 'semana':
            data_inicial = hoje - timedelta(weeks=4)
            data_final = hoje
        elif periodo == 'mes':
            data_inicial = hoje - timedelta(days=180)
            data_final = hoje
        elif periodo == 'ano':
            data_inicial = hoje - timedelta(days=365)
            data_final = hoje
    
    # Obter dados para gráficos
    dados = {
        'ordens_por_status': obter_ordens_por_status(condominio_id, data_inicial, data_final),
        'ordens_por_prioridade': obter_ordens_por_prioridade(condominio_id, data_inicial, data_final),
        'ordens_por_periodo': obter_ordens_por_periodo(condominio_id, data_inicial, data_final, periodo),
        'tempo_medio_conclusao': obter_tempo_medio_conclusao(condominio_id, data_inicial, data_final),
        'ordens_por_tipo': obter_ordens_por_tipo(condominio_id, data_inicial, data_final)
    }
    
    return jsonify(dados)


def obter_estatisticas_gerais(condominio_id=None):
    """Obtém estatísticas gerais para o dashboard."""
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
    ordens_aguardando = query.filter(
        OrdemServico.status.in_(['Aguardando Aprovação', 'Aguardando Material'])
    ).count()
    ordens_concluidas = query.filter_by(status='Concluída').count()
    ordens_canceladas = query.filter_by(status='Cancelada').count()
    
    # Calcular ordens por prioridade
    ordens_alta = query.filter_by(prioridade='Alta').count()
    ordens_normal = query.filter_by(prioridade='Normal').count()
    ordens_baixa = query.filter_by(prioridade='Baixa').count()
    
    # Calcular ordens recentes (últimos 30 dias)
    data_limite = datetime.now(FORTALEZA_TZ) - timedelta(days=30)
    ordens_recentes = query.filter(OrdemServico.data_criacao >= data_limite).count()
    
    # Calcular ordens concluídas recentemente (últimos 30 dias)
    ordens_concluidas_recentes = query.filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.data_conclusao >= data_limite
    ).count()
    
    return {
        'total_ordens': total_ordens,
        'ordens_abertas': ordens_abertas,
        'ordens_andamento': ordens_andamento,
        'ordens_aguardando': ordens_aguardando,
        'ordens_concluidas': ordens_concluidas,
        'ordens_canceladas': ordens_canceladas,
        'ordens_alta': ordens_alta,
        'ordens_normal': ordens_normal,
        'ordens_baixa': ordens_baixa,
        'ordens_recentes': ordens_recentes,
        'ordens_concluidas_recentes': ordens_concluidas_recentes
    }


def obter_ordens_por_status(condominio_id=None, data_inicial=None, data_final=None):
    """Obtém contagem de ordens por status."""
    # Construir query base
    query = db.session.query(
        OrdemServico.status,
        func.count(OrdemServico.id).label('total')
    ).group_by(OrdemServico.status)
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros adicionais
    if condominio_id:
        query = query.filter(OrdemServico.condominio_id == condominio_id)
    
    if data_inicial:
        query = query.filter(OrdemServico.data_criacao >= data_inicial)
    
    if data_final:
        query = query.filter(OrdemServico.data_criacao <= data_final)
    
    # Executar query
    resultados = query.all()
    
    # Formatar resultados
    dados = [{'status': r.status, 'total': r.total} for r in resultados]
    
    return dados


def obter_ordens_por_prioridade(condominio_id=None, data_inicial=None, data_final=None):
    """Obtém contagem de ordens por prioridade."""
    # Construir query base
    query = db.session.query(
        OrdemServico.prioridade,
        func.count(OrdemServico.id).label('total')
    ).group_by(OrdemServico.prioridade)
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros adicionais
    if condominio_id:
        query = query.filter(OrdemServico.condominio_id == condominio_id)
    
    if data_inicial:
        query = query.filter(OrdemServico.data_criacao >= data_inicial)
    
    if data_final:
        query = query.filter(OrdemServico.data_criacao <= data_final)
    
    # Executar query
    resultados = query.all()
    
    # Formatar resultados
    dados = [{'prioridade': r.prioridade, 'total': r.total} for r in resultados]
    
    return dados


def obter_ordens_por_periodo(condominio_id=None, data_inicial=None, data_final=None, periodo='mes'):
    """Obtém contagem de ordens por período (dia, semana, mês, ano)."""
    # Definir agrupamento com base no período
    if periodo == 'dia':
        # Agrupar por dia
        data_label = func.date(OrdemServico.data_criacao).label('periodo')
        format_str = '%Y-%m-%d'
    elif periodo == 'semana':
        # Agrupar por semana
        data_label = func.date_trunc('week', OrdemServico.data_criacao).label('periodo')
        format_str = '%Y-%m-%d'
    elif periodo == 'mes':
        # Agrupar por mês
        data_label = func.date_trunc('month', OrdemServico.data_criacao).label('periodo')
        format_str = '%Y-%m'
    else:  # ano
        # Agrupar por ano
        data_label = extract('year', OrdemServico.data_criacao).label('periodo')
        format_str = '%Y'
    
    # Construir query base
    query = db.session.query(
        data_label,
        OrdemServico.status,
        func.count(OrdemServico.id).label('total')
    ).group_by(data_label, OrdemServico.status).order_by(data_label)
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros adicionais
    if condominio_id:
        query = query.filter(OrdemServico.condominio_id == condominio_id)
    
    if data_inicial:
        query = query.filter(OrdemServico.data_criacao >= data_inicial)
    
    if data_final:
        query = query.filter(OrdemServico.data_criacao <= data_final)
    
    # Executar query
    resultados = query.all()
    
    # Organizar resultados por período e status
    dados_por_periodo = {}
    periodos_unicos = []
    status_unicos = []
    
    for r in resultados:
        periodo_str = r.periodo.strftime(format_str) if hasattr(r.periodo, 'strftime') else str(r.periodo)
        
        if periodo_str not in dados_por_periodo:
            dados_por_periodo[periodo_str] = {}
            periodos_unicos.append(periodo_str)
        
        dados_por_periodo[periodo_str][r.status] = r.total
        
        if r.status not in status_unicos:
            status_unicos.append(r.status)
    
    # Formatar para uso em gráficos
    periodos_unicos.sort()
    series = []
    
    for status in status_unicos:
        data = []
        for periodo_str in periodos_unicos:
            data.append(dados_por_periodo[periodo_str].get(status, 0))
        
        series.append({
            'name': status,
            'data': data
        })
    
    return {
        'categorias': periodos_unicos,
        'series': series
    }


def obter_tempo_medio_conclusao(condominio_id=None, data_inicial=None, data_final=None):
    """Obtém tempo médio de conclusão das ordens por tipo."""
    # Construir query base
    query = db.session.query(
        OrdemServico.tipo,
        func.avg(
            func.extract('epoch', OrdemServico.data_conclusao - OrdemServico.data_criacao) / 86400
        ).label('dias')
    ).filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.data_conclusao.isnot(None)
    ).group_by(OrdemServico.tipo)
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros adicionais
    if condominio_id:
        query = query.filter(OrdemServico.condominio_id == condominio_id)
    
    if data_inicial:
        query = query.filter(OrdemServico.data_conclusao >= data_inicial)
    
    if data_final:
        query = query.filter(OrdemServico.data_conclusao <= data_final)
    
    # Executar query
    resultados = query.all()
    
    # Formatar resultados
    dados = [{'tipo': r.tipo, 'dias': round(r.dias, 1) if r.dias else 0} for r in resultados]
    
    return dados


def obter_ordens_por_tipo(condominio_id=None, data_inicial=None, data_final=None):
    """Obtém contagem de ordens por tipo."""
    # Construir query base
    query = db.session.query(
        OrdemServico.tipo,
        func.count(OrdemServico.id).label('total')
    ).group_by(OrdemServico.tipo)
    
    # Filtrar por condomínios do usuário
    if not current_user.is_admin:
        query = query.filter(OrdemServico.condominio_id.in_([c.id for c in current_user.condominios]))
    
    # Aplicar filtros adicionais
    if condominio_id:
        query = query.filter(OrdemServico.condominio_id == condominio_id)
    
    if data_inicial:
        query = query.filter(OrdemServico.data_criacao >= data_inicial)
    
    if data_final:
        query = query.filter(OrdemServico.data_criacao <= data_final)
    
    # Executar query
    resultados = query.all()
    
    # Formatar resultados
    dados = [{'tipo': r.tipo, 'total': r.total} for r in resultados]
    
    return dados


@dashboard_bp.route('/relatorios')
@login_required
def relatorios():
    """Rota para relatórios."""
    return render_template('dashboard/relatorios.html', title='Relatórios')
