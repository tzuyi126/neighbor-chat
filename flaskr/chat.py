from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from flaskr.auth import login_required
from flaskr.db import fetch_all, fetch_one, execute
from flaskr.geolocate import find_coord

bp = Blueprint('chat', __name__)

@bp.route('/')
@login_required
def index():
    neighbor_list = fetch_all('''
            with neighbors(uid) as (
                select nuid from neighbor where uid = %s
            ),
            init_message(tid, uid) as (
                select distinct m.tid, m.uid from message m inner join neighbors n on n.uid = m.uid
                where reply_mid is null
            )
            select * from thread t inner join init_message im on t.tid = im.tid
            inner join users u on im.uid = u.uid
            where recipient != 'Users'
            ''', 
            (g.user['uid'],)
        )

    friend_list = fetch_all('''
            with friends(uid) as (
                select get_all_friends.id from get_all_friends(%s) where get_all_friends.status = 'Approved'
            ),
            init_message(tid, uid) as (
                select distinct m.tid, m.uid from message m inner join friends f on f.uid = m.uid
                where reply_mid is null
            )
            select * from thread t inner join init_message im on t.tid = im.tid
            inner join users u on im.uid = u.uid
            where recipient != 'Users'
            ''', 
            (g.user['uid'], )
        )
    
    block_list = fetch_all('''
            with accessible_block as (
                select uid, bid from blockmember
                where status = 'Approved' and uid = %s
                union
                select uid, bid from blockfollow
                where uid = %s
            ),
            accessible_thread as (
                select uid, tid, title, ttime
                from thread inner join accessible_block
                on recipient = 'Block' and recipient_id = bid
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            inner join message on accessible_thread.tid = message.tid''', 
            (g.user['uid'], g.user['uid'])
        )
    
    hood_list = fetch_all('''
            with accessible_hood as (
                select uid, hid from blockmember
                inner join block using(bid)
                where status = 'Approved' and uid = %s
            ),
            accessible_thread as (
                select uid, tid, title, ttime
                from thread inner join accessible_hood
                on recipient = 'Hood' and recipient_id = hid
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            inner join message on accessible_thread.tid = message.tid''', 
            (g.user['uid'],)
        )
    
    user_list = fetch_all('''
            with accessible_thread as (
                select distinct %s as uid, thread.tid, title, ttime
                from thread inner join message on thread.tid = message.tid
                where recipient = 'Users' and (thread.recipient_id = %s or
                message.uid = %s)
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            inner join message on accessible_thread.tid = message.tid
            ''', (g.user['uid'], g.user['uid'], g.user['uid']))
                   
    
    return render_template('chat/index.html',
                           neighbor_list=neighbor_list,
                           block_list=block_list,
                           hood_list=hood_list,
                           friend_list=friend_list,
                           user_list=user_list)

@bp.route('/filter', methods=['GET', 'POST'])
@login_required
def filter():

    geo_range = request.form.get('geo_range')

    user_lat, user_lon = g.user['ulatitude'], g.user['ulongitude']

    neighbor_list = fetch_all('''
            with neighbors(uid) as (
                select nuid from neighbor where uid = %s
            ),
            init_message(tid, uid, mlatitude, mlongitude) as (
                select distinct m.tid, m.uid, m.mlatitude, m.mlongitude 
                from message m inner join neighbors n on n.uid = m.uid
                where reply_mid is null
            )
            select * from thread t inner join init_message im on t.tid = im.tid
            inner join users u on im.uid = u.uid
            where recipient != 'Users' and im.mlongitude is not null and im.mlongitude is not null and
            (point(im.mlongitude, im.mlatitude) <@> point(%s, %s)) < %s
            ''', 
            (g.user['uid'], user_lon, user_lat, geo_range)
        )

    friend_list = fetch_all('''
            with friends(uid) as (
                select get_all_friends.id from get_all_friends(%s) where get_all_friends.status = 'Approved'
            ),
            init_message(tid, uid, mlatitude, mlongitude) as (
                select distinct m.tid, m.uid, m.mlatitude, m.mlongitude 
                from message m inner join friends f on f.uid = m.uid
                where reply_mid is null
            )
            select * from thread t inner join init_message im on t.tid = im.tid
            inner join users u on im.uid = u.uid
            where recipient != 'Users' and im.mlongitude is not null and im.mlongitude is not null and
            (point(im.mlongitude, im.mlatitude) <@> point(%s, %s)) < %s
            ''', 
            (g.user['uid'], user_lon, user_lat, geo_range)
        )
    
    block_list = fetch_all('''
            with accessible_block as (
                select uid, bid from blockmember
                where status = 'Approved' and uid = %s
                union
                select uid, bid from blockfollow
                where uid = %s
            ),
            accessible_thread as (
                select uid, tid, title, ttime
                from thread inner join accessible_block
                on recipient = 'Block' and recipient_id = bid
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            inner join message on accessible_thread.tid = message.tid
            where reply_mid is null and 
            mlongitude is not null and mlongitude is not null and
            (point(mlongitude, mlatitude) <@> point(%s, %s)) < %s''', 
            (g.user['uid'], g.user['uid'], user_lon, user_lat, geo_range)
        )
    
    hood_list = fetch_all('''
            with accessible_hood as (
                select uid, hid from blockmember
                inner join block using(bid)
                where status = 'Approved' and uid = %s
            ),
            accessible_thread as (
                select uid, tid, title, ttime
                from thread inner join accessible_hood
                on recipient = 'Hood' and recipient_id = hid
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            inner join message on accessible_thread.tid = message.tid
            where reply_mid is null and 
            mlongitude is not null and mlongitude is not null and
            (point(mlongitude, mlatitude) <@> point(%s, %s)) < %s''', 
            (g.user['uid'], user_lon, user_lat, geo_range)
        )
    
    user_list = fetch_all('''
            with accessible_thread as (
                select distinct %s as uid, thread.tid, title, ttime
                from thread inner join message on thread.tid = message.tid
                where recipient = 'Users' and (thread.recipient_id = %s or
                message.uid = %s)
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            inner join message on accessible_thread.tid = message.tid
            where reply_mid is null and 
            mlongitude is not null and mlongitude is not null and
            (point(mlongitude, mlatitude) <@> point(%s, %s)) < %s
            ''', (g.user['uid'], g.user['uid'], g.user['uid'], user_lon, user_lat, geo_range))
                   
    
    return render_template('chat/index.html',
                           neighbor_list=neighbor_list,
                           block_list=block_list,
                           hood_list=hood_list,
                           friend_list=friend_list,
                           user_list=user_list,
                           geo_range=geo_range)


@bp.route('/chat/unread', methods=["GET", "POST"])
@login_required
def unread():
    
    neighbor_list = fetch_all('''
            with neighbors(uid) as (
                select nuid from neighbor where uid = %s
            ),
            init_message(tid, uid) as (
                select distinct m.tid, m.uid from message m inner join neighbors n on n.uid = m.uid
                where reply_mid is null
            )
            select distinct u.uid, u.first_name, u.last_name, t.tid, t.title, t.ttime
            from thread t inner join init_message im on t.tid = im.tid
            left join read r on r.tid = t.tid and r.uid = %s
            inner join message m on m.tid = t.tid
            inner join users u on im.uid = u.uid
            where recipient != 'Users' and (m.post_time > r.last_time or r.last_time is null)
            ''', 
            (g.user['uid'], g.user['uid'])
        )

    friend_list = fetch_all('''
            with friends(uid) as (
                select get_all_friends.id from get_all_friends(%s) where get_all_friends.status = 'Approved'
            ),
            init_message(tid, uid) as (
                select distinct m.tid, m.uid from message m inner join friends f on f.uid = m.uid
                where reply_mid is null
            )
            select distinct u.uid, u.first_name, u.last_name, t.tid, t.title, t.ttime
            from thread t inner join init_message im on t.tid = im.tid
            left join read r on r.tid = t.tid and r.uid = %s
            inner join message m on m.tid = t.tid
            inner join users u on im.uid = u.uid
            where recipient != 'Users' and (m.post_time > r.last_time or r.last_time is null)
            ''', 
            (g.user['uid'], g.user['uid'])
        )
    
    block_list = fetch_all('''
            with accessible_block as (
                select uid, bid from blockmember
                where status = 'Approved' and uid = %s
                union
                select uid, bid from blockfollow
                where uid = %s
            ),
            accessible_thread as (
                select uid, tid, title, ttime
                from thread inner join accessible_block
                on recipient = 'Block' and recipient_id = bid
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            left join read using(uid, tid)
            inner join message on accessible_thread.tid = message.tid
            where post_time > last_time or last_time is null''', 
            (g.user['uid'], g.user['uid'])
        )
    
    hood_list = fetch_all('''
            with accessible_hood as (
                select uid, hid from blockmember
                inner join block using(bid)
                where status = 'Approved' and uid = %s
            ),
            accessible_thread as (
                select uid, tid, title, ttime
                from thread inner join accessible_hood
                on recipient = 'Hood' and recipient_id = hid
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            left join read using(uid, tid)
            inner join message on accessible_thread.tid = message.tid
            where post_time > last_time or last_time is null''', 
            (g.user['uid'],)
        )
    
    user_list = fetch_all('''
            with accessible_thread as (
                select distinct %s as uid, thread.tid, title, ttime
                from thread inner join message on thread.tid = message.tid
                where recipient = 'Users' and (thread.recipient_id = %s or
                message.uid = %s)
            )
            select distinct accessible_thread.tid, title, ttime from accessible_thread
            left join read using(uid, tid)
            inner join message on accessible_thread.tid = message.tid
            where post_time > last_time or last_time is null
            ''', (g.user['uid'], g.user['uid'], g.user['uid']))
                            
    return render_template("chat/unread.html", 
                           neighbor_list=neighbor_list,
                           friend_list=friend_list,
                           block_list=block_list, 
                           hood_list=hood_list,
                           user_list=user_list)

def get_dropdown_values():
    recipient_types = ['Users', 'Block', 'Hood']

    # Create an empty dictionary
    entries = {}

    for type in recipient_types:
        if type == 'Users':
            recipient_list = fetch_all('''
                        select distinct email as name 
                        from users inner join get_all_friends(%s) 
                        on get_all_friends.id = users.uid
                        where status = 'Approved'
                    ''', (g.user['uid'], ))
        elif type == 'Block':
            recipient_list = fetch_all('''
                        select distinct b.bname as name
                        from block b inner join blockmember bm on b.bid = bm.bid
                        where bm.uid = %s and status = 'Approved'
                    ''', (g.user['uid'],))
        else:
            recipient_list = fetch_all('''
                        select distinct h.hname as name
                        from hood h inner join block b on h.hid = b.hid
                        inner join blockmember bm on b.bid = bm.bid
                        where bm.uid = %s and status = 'Approved'
                    ''', (g.user['uid'],))
    
        # build the structure (lst_c) that includes the names of the car models that belong to the car brand
        type_recipient_list = []
        for recipient in recipient_list:
            type_recipient_list.append(recipient)
        entries[type] = type_recipient_list
    
    class_entry_relations = entries
    return class_entry_relations

@bp.route('/chat/_update_dropdown')
@login_required
def update_dropdown():

    # the value of the first dropdown (selected by the user)
    selected_class = request.args.get('selected_class', type=str)
    # get values for the second dropdown
    updated_values = get_dropdown_values()[selected_class]

    # create the value sin the dropdown as a html string
    html_string_selected = ''
    for entry in updated_values:
        entry = entry['name']
        html_string_selected += '<option value="{}">{}</option>'.format(entry, entry)

    return jsonify(html_string_selected=html_string_selected)

@bp.route('/chat/create', methods=["GET", "POST"])
@login_required
def create():
    class_entry_relations = get_dropdown_values()

    default_classes = sorted(class_entry_relations.keys())
    default_values = [row['name'] for row in class_entry_relations[default_classes[0]]]
    if request.method=='POST':
        
        title = request.form.get('title')
        text_body = request.form.get('text_body')
        recipient = request.form.get('recipient')
        recipient_name = request.form.get('recipient_name')

        loc_street = request.form.get('loc_street')
        loc_city = request.form.get('loc_city')
        loc_state = request.form.get('loc_state')
        loc_zip = request.form.get('loc_zip')
        
        recipient_id = get_recipient_id(recipient, recipient_name)

        error = None

        if not title:
            error = 'Please enter a title.'
        elif not text_body:
            error = 'Please enter the text body.'
        elif not recipient_id:
            error = 'Could not find the correct recipient. Please specify the correct user email, block name, or hood name.'
        elif recipient_id == g.user['uid'] and recipient == 'Users':
            error = 'Could not create a thread with yourself.'

        lat, lon = None, None
        
        if loc_street and loc_city and loc_state and loc_zip:
            try:
                lat, lon = find_coord(loc_street, loc_city, loc_state, loc_zip)
            except:
                error = 'Please provide valid address.'

        params=[title, recipient, recipient_id, g.user['uid'], text_body, g.user['uid'], lat, lon]

        if error is None:
            try:
                execute( '''
                    with t(tid) as (
                        insert into thread(ttime, title, recipient, recipient_id)
                        values(now(), %s, %s, %s)
                        returning tid
                    ), read as (
                        insert into read (uid, last_time, tid) 
                        select %s, now(), tid from t
                    )
                    insert into message(post_time, text_body, uid, mlatitude, mlongitude, tid)
                    select now(), %s, %s, %s, %s, tid from t;''', 
                    params
                )
                
            except Exception as e:
                error = e
            else:
                flash('You created a thread.')
                return redirect(url_for('index'))
    
        flash(error)

    return render_template('chat/create.html',
                        all_classes=default_classes,
                        all_entries=default_values)

@bp.route('/chat/message/<int:tid>', methods=["GET", "POST"])
@login_required
def message(tid):
    thread_detail = fetch_one('''
            select * from thread where tid = %s
            ''', (tid,))
    
    recipient = thread_detail['recipient']

    recipient_name = None
    if recipient == 'Users':
        if thread_detail['recipient_id'] == g.user['uid']:
            init_message = fetch_one('''
                select * from message where tid = %s and reply_mid is null
            ''', (thread_detail['tid'],))

            recipient_name = fetch_one('''
                select first_name, last_name from users where uid = %s
                ''', (init_message['uid'],))
        else:
            recipient_name = fetch_one('''
                select first_name, last_name from users where uid = %s
                ''', (thread_detail['recipient_id'],))
        
        recipient_name = ' '.join([recipient_name['first_name'], recipient_name['last_name']])
    elif recipient == 'Block':
        recipient_name = fetch_one('''
            select bname from block where bid = %s
            ''', (thread_detail['recipient_id'],))['bname']
    elif recipient == 'Hood':
        recipient_name = fetch_one('''
            select hname from hood where hid = %s
            ''', (thread_detail['recipient_id'],))['hname']
    
    message_list = fetch_all('''
                with temp as (select mid, uid, first_name, text_body, post_time, mlatitude, mlongitude, reply_mid
                    from message inner join users using (uid)
                    where tid = %s
                )
                select t1.mid as mid, t1.uid as uid, t1.first_name as post_name, t1.text_body as text_body, 
                    t1.post_time as post_time, t1.mlatitude as mlatitude, t1.mlongitude as mlongitude, t2.first_name as reply_to_name
                from temp as t1 left join temp as t2 on t1.reply_mid = t2.mid order by t1.post_time''', 
                (tid, )
    )

    execute('''
        insert into read (uid, tid, last_time) values(%s, %s, now())
        on conflict (uid, tid)
        do update set last_time = now()
    ''', (g.user['uid'], tid))
    
    return render_template("chat/message.html", message_list=message_list, thread_detail=thread_detail, recipient_name=recipient_name)

@bp.route('/chat/message/reply/<int:mid>', methods=["GET", "POST"])
@login_required
def reply(mid):
    
    tid = fetch_one('''
            select tid from message where mid = %s
            ''', (mid,))
    
    if request.method == "GET":
        message_details = fetch_one('''
                with temp as (select mid, first_name, text_body, post_time, mlatitude, mlongitude, reply_mid
                        from message inner join users using (uid)
                        where mid=%s
                )
                select t1.mid as mid, t1.first_name as post_name, t1.text_body as text_body, t1.post_time as post_time, 
                        t1.mlatitude as mlatitude, t1.mlongitude as mlongitude, t2.first_name as reply_to_name
                from temp as t1 left join temp as t2 on t1.reply_mid = t2.mid;''', 
                (mid,)
        )

        return render_template('chat/reply.html', message_details=message_details, tid=tid['tid'])

    
    text_body = request.form.get('text_body_')

    loc_street = request.form.get('loc_street')
    loc_city = request.form.get('loc_city')
    loc_state = request.form.get('loc_state')
    loc_zip = request.form.get('loc_zip')

    error = None
    lat, lon = None, None
        
    if loc_street and loc_city and loc_state and loc_zip:
        try:
            lat, lon = find_coord(loc_street, loc_city, loc_state, loc_zip)
        except:
            error = 'Please provide valid address.'

    execute('''
            insert into message(post_time, text_body, uid, tid, mlatitude, mlongitude, reply_mid)
            values(now(), %s, %s, %s, %s, %s, %s);''', 
            (text_body, g.user['uid'], tid['tid'], lat, lon, mid))
    
    return redirect(url_for("chat.message", tid=tid['tid']))
        
@bp.route('/chat/message/delete/<int:mid>', methods=["GET","POST"])
@login_required
def delete(mid):
    execute('''
            update message
            set text_body='[DELETED]'
            where mid=%s''', (mid, ))
    
    return redirect(request.referrer)

@bp.route('/chat/message/search', methods=["GET","POST"])
@login_required
def search():

    keyword = request.form.get('keyword')
    
    neighbor_list = fetch_all('''
            with neighbors(uid) as (
                select nuid from neighbor where uid = %s
            ),
            init_message(tid, mid, uid) as (
                select m.tid, m.mid, m.uid from message m inner join neighbors n on n.uid = m.uid
            )
            select distinct m.mid, m.tid, m.uid, first_name, post_time, text_body, mlatitude, mlongitude, reply_mid 
            from init_message inner join message m on init_message.mid = m.mid
            inner join users on init_message.uid = users.uid
            inner join thread on thread.tid = init_message.tid
            where recipient != 'Users' and text_body ilike %s order by post_time
            ''', (g.user['uid'], '%' + keyword + '%'))

    friend_list = fetch_all('''
            with friends(uid) as (
                select get_all_friends.id from get_all_friends(%s) where get_all_friends.status = 'Approved'
            ),
            init_message(tid, mid, uid) as (
                select m.tid, m.mid, m.uid from message m inner join friends f on f.uid = m.uid
            )
            select distinct m.mid, m.tid, m.uid, first_name, post_time, text_body, mlatitude, mlongitude, reply_mid 
            from init_message inner join message m on init_message.mid = m.mid
            inner join users on init_message.uid = users.uid
            inner join thread on thread.tid = init_message.tid
            where recipient != 'Users' and text_body ilike %s order by post_time
            ''', (g.user['uid'], '%' + keyword + '%'))
    

    block_list = fetch_all('''
            with accessible_block as (
                select uid, bid from blockmember
                where status = 'Approved' and uid = %s
                union
                select uid, bid from blockfollow
                where uid = %s
            ),
            accessible_thread as (
                select uid, tid
                from thread inner join accessible_block
                on recipient = 'Block' and recipient_id = bid
            )
            select distinct message.mid, message.tid, message.uid, first_name, post_time, text_body, mlatitude, mlongitude, reply_mid
            from accessible_thread
            inner join message on accessible_thread.tid = message.tid and text_body ilike %s
            inner join users on message.uid = users.uid order by post_time
            ''', (g.user['uid'], g.user['uid'], '%' + keyword + '%'))
    
    hood_list = fetch_all('''
            with accessible_hood as (
                select uid, hid from blockmember
                inner join block using(bid)
                where status = 'Approved' and uid = %s
            ),
            accessible_thread as (
                select uid, tid
                from thread inner join accessible_hood
                on recipient = 'Hood' and recipient_id = hid
            )
            select distinct message.mid, message.tid, message.uid, first_name, post_time, text_body, mlatitude, mlongitude, reply_mid 
            from accessible_thread
            inner join message on accessible_thread.tid = message.tid and text_body ilike %s
            inner join users on message.uid = users.uid order by post_time
            ''', (g.user['uid'], '%' + keyword + '%'))
    
    user_list = fetch_all('''
            with accessible_thread as (
                select distinct %s as uid, thread.tid, title, ttime
                from thread inner join message on thread.tid = message.tid
                where recipient = 'Users' and (thread.recipient_id = %s or
                message.uid = %s)
            )
            select distinct message.mid, message.tid, message.uid, first_name, post_time, text_body, mlatitude, mlongitude, reply_mid 
            from accessible_thread
            inner join message on accessible_thread.tid = message.tid and text_body ilike %s
            inner join users on message.uid = users.uid order by post_time
            ''', (g.user['uid'], g.user['uid'], g.user['uid'], '%' + keyword + '%'))
                                
    return render_template("chat/searchresult.html", 
                           neighbor_list=neighbor_list,
                           friend_list=friend_list,
                           block_list=block_list,
                           hood_list=hood_list, 
                           user_list=user_list,
                           keyword=keyword)



def get_recipient_id(recipient, recipient_name):
    recipient_ids = None

    if recipient == 'Users':
        recipient_ids = fetch_all(
            '''select distinct uid as id from users where email like %s''',
            ('%'+ recipient_name + '%',)
        )
    elif recipient == 'Block':
        recipient_ids = fetch_all(
            '''select distinct bid as id from block where bname like %s''',
            ('%'+ recipient_name + '%',)
        )
    elif recipient == 'Hood':
        recipient_ids = fetch_all(
            '''select distinct hid as id from hood where hname like %s''',
            ('%'+ recipient_name + '%',)
        )
    
    if not recipient_ids:
        return None
    elif len(recipient_ids) > 1:
        return None
    
    return recipient_ids[0]['id']