from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from flaskr.auth import login_required
from flaskr.db import fetch_all, fetch_one, execute

bp = Blueprint('block', __name__)

@bp.route('/block')
@login_required
def block():
    
    hoods = fetch_all(
        'select * from hood', ()
    )

    blocks = fetch_all(
        'SELECT * FROM Block', ()
    )

    block_member = fetch_one(
        'SELECT * FROM blockmember inner join block using(bid) WHERE uid = %s',
        (g.user['uid'],)
    )

    block_feeds = None
    if block_member and block_member['status'] == 'Approved':
        block_feeds = fetch_all(
            'select * from thread where recipient = %s and recipient_id = %s', 
            ('Block', block_member['bid'])
        )

    approvals = fetch_all('''
        with member(bid) as (
            select bid from blockmember where uid = %s and status = 'Approved'
        ), waiting(bid, uid) as (
            select bm.bid, bm.uid from blockmember bm
            inner join member on bm.bid = member.bid
            where bm.uid != %s and bm.status = 'InProgress'
        ), approved(auid) as (
            select auid from blockmemberapproval inner join member using(bid)
            where uid = %s
        )
        select * from waiting inner join users on waiting.uid = users.uid where
        waiting.uid not in (select auid from approved)
        ''',
        (g.user['uid'], g.user['uid'], g.user['uid'])
    )

    block_follow = fetch_all(
        'SELECT bid FROM blockfollow WHERE uid = %s',
        (g.user['uid'],)
    )

    follow_list = []
    for block in block_follow:
        follow_list.append(block['bid'])

    return render_template('member/block.html', hoods=hoods, blocks=blocks, block_member=block_member, block_feeds=block_feeds, 
                           approvals=approvals, follow_list=follow_list)

@bp.route('/block/<int:bid>')
@login_required
def block_member(bid):
    
    block = fetch_one(
        'SELECT * FROM Block where bid = %s', (bid,)
    )

    block_members = fetch_all(
        '''SELECT * FROM blockmember inner join users using(uid)
        where bid = %s and status = 'Approved'
        ''', (bid,)
    )

    return render_template('member/blockmember.html', block=block, block_members=block_members)

@bp.route('/apply/block/<int:id>', methods=['POST'])
@login_required
def apply_block(id):
    error = None

    uid = g.user['uid']
    bid = id

    try:
        execute(
            'INSERT INTO blockmember (uid, bid, join_time, status) VALUES(%s, %s, now(), %s)', 
            (uid, bid, 'InProgress')
        )

    except Exception as e:
        print(e)
        error = 'Failed to apply a block.'
    
    if not error:
        flash('You applied a block.')
    else:
        flash(error)
    return redirect(request.referrer)

@bp.route('/approve/block/<int:bid>/<int:auid>', methods=['POST'])
@login_required
def approve_member(bid, auid):
    error = None

    uid = g.user['uid']

    try:
        execute(
            'INSERT INTO BlockMemberApproval (uid, bid, auid) VALUES(%s, %s, %s)', 
            (uid, bid, auid)
        )
        execute(
            'update blockmember set approval_num = approval_num + 1 where uid = %s and bid = %s;', 
            (auid, bid)
        )

    except Exception as e:
        print(e)
        error = 'Failed to approve a member.'
    
    if not error:
        flash('You approved a member.')
    else:
        flash(error)
    return redirect(request.referrer)

@bp.route('/delete/block/<int:id>', methods=['POST'])
@login_required
def delete_block(id):
    
    error = None

    uid = g.user['uid']
    bid = id

    try:
        execute(
            'DELETE FROM blockmember WHERE uid = %s AND bid = %s', 
            (uid, bid)
        )

    except:
        error = 'Failed to quit a block.'
    
    if not error:
        flash('You quit a block.')
    else:
        flash(error)

    return redirect(request.referrer)

@bp.route('/follow/block/<int:id>', methods=['POST'])
@login_required
def follow_block(id):
    
    error = None

    uid = g.user['uid']
    bid = id

    try:
        execute(
            'INSERT INTO blockfollow (uid, bid, follow_time) VALUES(%s, %s, now())', (uid, bid)
        )

    except Exception as e:
        error = 'Failed to follow a block.'
    
    if not error:
        flash('You followed a block.')
    else:
        flash(error)
    return redirect(request.referrer)

@bp.route('/unfollow/block/<int:id>', methods=['POST'])
@login_required
def unfollow_block(id):
    
    error = None

    uid = g.user['uid']
    bid = id

    try:
        execute(
            'DELETE FROM blockfollow WHERE uid = %s AND bid = %s', 
            (uid, bid)
        )

    except:
        error = 'Failed to unfollow a block.'
    
    if not error:
        flash('You unfollowed a block.')
    else:
        flash(error)

    return redirect(request.referrer)