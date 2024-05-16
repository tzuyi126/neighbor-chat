from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from flaskr.auth import login_required
from flaskr.db import fetch_all, fetch_one, execute

bp = Blueprint('friends', __name__)

@bp.route('/user/self')
@login_required
def user_self():
    return render_template('member/user.html', user=g.user)

@bp.route('/user/<int:id>')
@login_required
def user(id):
    user_id = g.user['uid']
    other_id = id

    user = fetch_one(
            'SELECT * FROM Users WHERE uid = %s', 
            (other_id,)
        )
    
    application = fetch_one(
            'SELECT status FROM Friend WHERE uid = %s AND fuid = %s',
            (user_id, other_id)
        )

    approval = fetch_one(
            'SELECT status FROM Friend WHERE uid = %s AND fuid = %s',
            (other_id, user_id)
        )

    neighbor_status = fetch_one(
            'SELECT * FROM Neighbor WHERE uid = %s AND nuid = %s',
            (user_id, other_id)
        )
    
    return render_template('member/user.html', user=user, application=application, approval=approval, neighbor_status=neighbor_status)

@bp.route('/friends')
@login_required
def friends():
    
    friends = fetch_all(
            'SELECT * FROM Users inner join get_all_friends(%s) on get_all_friends.id = Users.uid '
            'WHERE get_all_friends.status = %s', 
            (g.user['uid'], 'Approved')
        )
    
    approvals = fetch_all(
            'SELECT * FROM Users u inner join Friend f on u.uid = f.uid '
            'WHERE f.fuid = %s and f.status = %s', 
            (g.user['uid'], 'InProgress')
        )
    
    applying = fetch_all(
            'SELECT * FROM Users u inner join Friend f on u.uid = f.fuid '
            'WHERE f.uid = %s and f.status = %s', 
            (g.user['uid'], 'InProgress')
        )
    
    recommend = fetch_all(
            '(SELECT * FROM Users WHERE uid != %s AND '
            'uid not in (SELECT get_all_friends.id FROM get_all_friends(%s)) '
            'ORDER BY random() LIMIT 5)'
            , (g.user['uid'], g.user['uid'])
        )

    return render_template('member/friends.html', friends=friends, approvals=approvals, applying=applying, recommend=recommend)

@bp.route('/add/friend/<int:id>', methods=['POST'])
@login_required
def add_friend(id):
    error = None

    uid = g.user['uid']
    fuid = id

    try:
        execute(
            'INSERT INTO Friend (uid, fuid, status) VALUES(%s, %s, %s)', (uid, fuid, 'InProgress')
        )

    except:
        error = 'Failed to add a friend.'
    
    if not error:
        flash('You added a friend.')
    else:
        flash(error)
    return redirect(request.referrer)

@bp.route('/approve/friend/<int:id>', methods=['POST'])
@login_required
def approve_friend(id):
    
    error = None

    uid = id
    fuid = g.user['uid']

    try:
        execute(
            'UPDATE Friend SET status = %s '
            'WHERE uid = %s and fuid = %s', 
            ('Approved', uid, fuid)
        )

    except Exception as e:
        error = 'Failed to approve a friend.'
    
    if not error:
        flash('You approved the application.')
    else:
        flash(error)

    return redirect(request.referrer)

@bp.route('/delete/friend/<int:id>', methods=['POST'])
@login_required
def delete_friend(id):
    
    error = None

    uid = g.user['uid']
    fuid = id

    try:
        execute(
            'DELETE FROM Friend WHERE (uid = %s AND fuid = %s) '
            'OR (uid = %s AND fuid = %s)', 
            (uid, fuid, fuid, uid)
        )

    except:
        error = 'Failed to delete a friend.'
    
    if not error:
        flash('You deleted a friend.')
    else:
        flash(error)

    return redirect(request.referrer)
