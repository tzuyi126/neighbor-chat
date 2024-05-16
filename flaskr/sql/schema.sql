drop table if exists read;
drop table if exists blockfollow;
drop table if exists blockmemberapproval;
drop table if exists blockmember;
drop table if exists message;
drop table if exists thread;
drop table if exists block;
drop table if exists hood;
drop table if exists neighbor;
drop table if exists friend;
drop table if exists users;

create table Users(
    uid serial,
    password varchar(16) not null,
    first_name varchar(50) not null,
    last_name varchar(50) not null,
    profile varchar(4000),
    email varchar(50) unique not null,
    phone_number varchar(15),
    addr_street varchar(50),
    addr_city varchar(20),
    addr_state varchar(20),
    addr_zip varchar(5),
    ulatitude float,
    ulongitude float,
    primary key (uid)
);

create table Friend(
    uid int,
    fuid int,
    status varchar(10) not null,
    primary key (uid, fuid),
    foreign key (uid) references Users(uid),
    foreign key (fuid) references Users(uid)
);

create table Neighbor(
    uid int,
    nuid int,
    primary key (uid, nuid),
    foreign key (uid) references Users(uid),
    foreign key (nuid) references Users(uid)
);

create table Hood(
    hid serial,
    hname varchar(20),
    hlatitude float,
    hlongitude float,
    hradius float,
    primary key (hid)
);

create table Block(
    bid serial,
    bname varchar(20),
    blatitude float,
    blongitude float,
    bradius float,
    hid int not null,
    primary key (bid),
    foreign key (hid) references Hood(hid)
);

create table Thread(
    tid serial,
    ttime timestamp not null,
    title varchar(100),
    recipient varchar(10) not null,
    recipient_id int not null,
    primary key (tid)
);

create table Message(
    mid serial,
    post_time timestamp not null,
    text_body varchar(4000) not null,
    uid int not null,
    tid int not null,
    mlatitude float,
    mlongitude float,
    reply_mid int,
    primary key (mid),
    foreign key (uid) references Users(uid),
    foreign key (tid) references Thread(tid),
    foreign key (reply_mid) references Message(mid)
);

create table Read(
    uid int,
    tid int,
    last_time timestamp,
    primary key (uid, tid),
    foreign key (uid) references Users(uid),
    foreign key (tid) references Thread(tid)
);

create table BlockMember(
    uid int,
    bid int not null,
    join_time timestamp not null,
    status varchar(10) not null,
    approval_num int default 0,
    primary key (uid),
    foreign key (uid) references Users(uid),
    foreign key (bid) references Block(bid)
);

create table BlockMemberApproval(
    uid int,
    bid int,
    auid int,
    primary key (uid, bid, auid),
    foreign key (uid) references Users(uid),
    foreign key (bid) references Block(bid)
);

create table BlockFollow(
    uid int,
    bid int,
    follow_time timestamp not null,
    primary key (uid, bid),
    foreign key (uid) references Users(uid),
    foreign key (bid) references Block(bid)
);

/* Find all feeds for a specific user */
create or replace function all_feeds(param_uid INT)
    returns table (feeds_uid int, feeds_tid int, feeds_mid int)
    as $$
begin
    return query
    with accessible_block as (
        select uid, bid from blockmember
        where status = 'Approved' and uid = param_uid
        union
        select uid, bid from blockfollow
        where uid = param_uid
    ),
    accessible_block_thread as (
        select uid, tid
        from thread inner join accessible_block
        on recipient = 'Block' and recipient_id = bid
    ),
    accessible_block_message as (
        select abt.uid, abt.tid, message.mid from accessible_block_thread abt
        inner join message on abt.tid = message.tid
    ),
    accessible_hood as (
        select uid, hid from blockmember
        inner join block using(bid)
        where status = 'Approved' and uid = param_uid
    ),
    accessible_hood_thread as (
        select uid, tid
        from thread inner join accessible_hood
        on recipient = 'Hood' and recipient_id = hid
    ),
    accessible_hood_message as (
        select aht.uid, aht.tid, message.mid from accessible_hood_thread aht
        inner join message on aht.tid = message.tid
    ),
    accessible_direct_thread as (
        select distinct param_uid as uid, thread.tid
        from thread inner join message on thread.tid = message.tid
        where recipient = 'Users' and (thread.recipient_id = param_uid or message.uid = param_uid)
    ),
    accessible_direct_message as (
        select adt.uid, adt.tid, message.mid from accessible_direct_thread adt
        inner join message on adt.tid = message.tid
    ),
    all_feeds as (
        select * from accessible_block_message
        union
        select * from accessible_hood_message
        union
        select * from accessible_direct_message
    )
    select uid, tid, mid from all_feeds;
end;
$$
LANGUAGE 'plpgsql';

create or replace function get_all_friends(param_uid INT)
    returns table (id int, status VARCHAR)
    as $$
begin
    return query
    (SELECT f.fuid, f.status FROM Friend f WHERE f.uid = param_uid) 
    UNION 
    (SELECT f.uid, f.status FROM Friend f WHERE f.fuid = param_uid);
end;
$$
LANGUAGE 'plpgsql';

/* if a block member approves an application, check if the application reaches the threshold */
create or replace function approve_block_member()
    returns trigger
    as $$
declare 
    approval_threshold INT;
    member_status VARCHAR(10);
begin
    if TG_OP = 'UPDATE' then
        select bm.status into member_status
        from BlockMember bm 
        where bm.bid = NEW.bid and bm.uid = NEW.uid;

        if member_status = 'Approved' then
            raise exception 'Block member has already been approved.';
        end if;
    end if;

    select count(*) into approval_threshold
    from BlockMember bm 
    where bm.bid = NEW.bid and bm.status = 'Approved'
    group by bm.bid;

    if approval_threshold is null then
        raise notice 'Member is the first member to join the block.';
        
        NEW.status := 'Approved';
    elsif approval_threshold < 3 then
        if NEW.approval_num >= approval_threshold then
            raise notice 'Block member approved! approval_num: "%" is greater than or equal to threshold: "%"', new.approval_num, approval_threshold;

            NEW.status := 'Approved';
        end if;
    else
        if NEW.approval_num >= 3 then
            raise notice 'Block member approved! approval_num: "%" is greater than or equal to 3', new.approval_num;

            NEW.status := 'Approved';
        end if;
    end if;
    
    return NEW;
end;
$$
LANGUAGE 'plpgsql';

create trigger block_member_approval
before insert or update on BlockMember
for each row
execute function approve_block_member();

/* if a user cancels the block member application, delete existing approval */
create or replace function delete_block_member_approval()
    returns trigger
    as $$
begin
    delete from BlockMemberApproval
    where bid = OLD.bid and uid = OLD.uid;

    return NULL;
end;
$$
LANGUAGE 'plpgsql';

create trigger block_member_cancelled
after delete on BlockMember
for each row
execute function delete_block_member_approval();