from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from flaskr.auth import login_required
from flaskr.db import fetch_all, fetch_one, execute

bp = Blueprint('neighbors', __name__)

@bp.route('/neighbors')
@login_required
def neighbors():

    users = fetch_all(
        '''select * from users where uid != %s''', (g.user['uid'],)
    )
    
    neighbors = fetch_all(
            'SELECT nuid FROM neighbor WHERE uid = %s', 
            (g.user['uid'], )
        )
    
    neighbor_list = [row['nuid'] for row in neighbors]
    
    return render_template('member/neighbors.html', users=users, neighbor_list=neighbor_list)

@bp.route('/follow/neighbor/<int:id>', methods=['POST'])
@login_required
def add_neighbor(id):
    
    error = None

    uid = g.user['uid']
    nuid = id

    try:
        execute(
            'INSERT INTO Neighbor (uid, nuid) VALUES(%s, %s)', (uid, nuid)
        )

    except Exception as e:
        error = 'Failed to follow a user.'
    
    if not error:
        flash('You followed a user.')
    else:
        flash(error)
    return redirect(request.referrer)

@bp.route('/unfollow/neighbor/<int:id>', methods=['POST'])
@login_required
def unfollow_neighbor(id):
    
    error = None

    uid = g.user['uid']
    nuid = id

    try:
        execute(
            'DELETE FROM Neighbor WHERE uid = %s AND nuid = %s', 
            (uid, nuid)
        )

    except:
        error = 'Failed to unfollow a user.'
    
    if not error:
        flash('You unfollowed a user.')
    else:
        flash(error)

    return redirect(request.referrer)