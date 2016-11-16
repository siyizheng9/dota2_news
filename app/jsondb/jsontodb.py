import json
from .. import create_app, db
from ..models import User, Role, News, Player, Team, Comment

db.create_all()

with open('./app/jsondb/teams.json') as data_file:
    data = json.load(data_file)

for team in data:
    teamname = team['TeamName']
    introduction = team['introduction']
    image = team['TeamLogo']
    teammember1 = team['TeamMember1']
    teammember2 = team['TeamMember2']
    teammember3 = team['TeamMember3']
    teammember4 = team['TeamMember4']
    teammember5 = team['TeamMember5']
    # print 'teamname: %s \n introduction: %s \n teammember1: %s\n \
    # teammember2: %s\nteammember3: %s\nteammember4: %s\nteammember5: %s\n' % \
    # (teamname, introduction, teammember1, teammember2, teammember3, teammember4, teammember5)

    t = Team(name=teamname, introduction=introduction, image=image)
    p1 = Player(name=teammember1)
    p2 = Player(name=teammember2)
    p3 = Player(name=teammember3)
    p4 = Player(name=teammember4)
    p5 = Player(name=teammember5)
    t.players.append(p1)
    t.players.append(p2)
    t.players.append(p3)
    t.players.append(p4)
    t.players.append(p5)
    db.session.add(t)
    db.session.add(p1)
    db.session.add(p2)
    db.session.add(p3)
    db.session.add(p4)
    db.session.add(p5)
db.session.commit()

with open('./app/jsondb/players.json') as data_file:
    data = json.load(data_file)

for player in data:
    playerid = player['PlayerID']
    introduction = player['Introduction']
    image = player['photo']
    teamname = player['Teamname']
    p = Player.query.filter_by(name=playerid).first()
    p.introduction = introduction
    p.image = image
    db.session.add(p)
db.session.commit()

    # print 'PlayerID: %s\n Introduction: %s\n Teamname: %s\n' % \
    # (playerid, introduction, teamname)

with open('./app/jsondb/news.json') as data_file:
    data = json.load(data_file)

for news in data:
    newsid = news['NewsID']
    title = news['Title']
    content = news['Content']
    relatedpalyer = news['RelatedPlayer']
    relatedteam = news['RelatedTeam']
    originalsource = news['OriginalSource']
    image = news['picture']

    n = News(title=title, content=content, original_source=originalsource, image=image)
    p = Player.query.filter_by(name=relatedpalyer).first()
    t = Team.query.filter_by(name=relatedteam).first()
    n.related_players.append(p)
    n.related_teams.append(t)
    db.session.add(n)
db.session.commit()

    # print 'NewsID: %s\nTitle: %s\nContent: %s\nRelatedPlayer: %s\n RelatedTeam: %s\nOriginalSource: %s\n' % \
    # (newsid, title, content, relatedpalyer, relatedteam, originalsource)

with open('./app/jsondb/users.json') as data_file:
    data = json.load(data_file)

for user in data:
    userid = user['SerialNumber']
    username = user['Username']
    password = user['Password']
    email = user['E-mail']
    favouriteplayer = user['FavouritePlayer']

    u = User(username=username, email=email, password_hash=password)
    db.session.add(u)
db.session.commit()

    # print 'userid: %s\nusername: %s\npassword: %s\nemail: %s\nfavouritepalyer: %s\n' % \
    #     (userid, username, password, email, favouriteplayer)

with open('./app/jsondb/comments.json') as data_file:
    data = json.load(data_file)

for cm in data:
    commentid = cm['SerialNumber']
    userid = cm['UserID']
    newsid = cm['NewsID']
    comment = cm['Comment']

    c = Comment(body=comment)
    u = User.query.filter_by(id=userid).first()
    n = News.query.filter_by(id=newsid).first()
    c.news = n
    c.author = u
    db.session.add(c)
db.session.commit()

    # print 'commentid: %s\nuserid: %s\nnewsid: %s\ncomment: %s\n' %\
    #     (commentid, userid, newsid, comment)
