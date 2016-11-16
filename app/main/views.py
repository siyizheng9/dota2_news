from flask import render_template, session, redirect, url_for, current_app, send_from_directory, request
from .. import db
from ..models import User, News, Player, Team
from ..email import send_email
from . import main
from .forms import NameForm
from .. import admin
from flask_admin.contrib.sqla import ModelView


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Player, db.session))
admin.add_view(ModelView(Team, db.session))


@main.route('/')
def index():
    return redirect(url_for('.news'))


@main.route('/news_detail/<int:id>', methods=['GET', 'POST'])
def news_detail(id):
    news = News.query.get_or_404(id)
    return render_template('news_detail.html', news=news)


@main.route('/news')
def news():
    page = request.args.get('page', 1, type=int)
    pagination = News.query.order_by(News.timestamp.desc()).paginate(
        page, per_page=12, error_out=True)
    news = pagination.items
    chunks = [news[i:i + 3] for i in range(0, len(news), 3)]
    return render_template('home.html', chunks=chunks, pagination=pagination)


@main.route('/players')
def players():
    page = request.args.get('page', 1, type=int)
    pagination = Player.query.order_by().paginate(
        page, per_page=12, error_out=True)
    players = pagination.items
    chunks = [players[i:i + 3] for i in range(0, len(players), 3)]
    return render_template('players.html', chunks=chunks,
                           pagination=pagination)


@main.route('/playerinfo/<int:id>')
def playerinfo(id):
    player = Player.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = player.news.order_by(News.timestamp.desc()).paginate(
        page, per_page=12, error_out=True)
    news = pagination.items
    return render_template('playerInfo.html', player=player, news=news,
                           pagination=pagination)


@main.route('/teams')
def teams():
    page = request.args.get('page', 1, type=int)
    pagination = Team.query.order_by().paginate(
        page, per_page=12, error_out=True)
    teams = pagination.items
    chunks = [teams[i:i + 3] for i in range(0, len(teams), 3)]
    return render_template('teams.html', chunks=chunks, pagination=pagination)


@main.route('/teaminfo/<int:id>')
def teaminfo(id):
    team = Team.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = team.news.order_by(News.timestamp.desc()).paginate(
        page, per_page=12, error_out=True)
    news = pagination.items
    return render_template('teamInfo.html', team=team, news=news,
                           pagination=pagination)


@main.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')
