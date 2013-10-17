#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
  mailchimp-invitation.py [options] set <email>
  mailchimp-invitation.py [options] setgroup <group>
  mailchimp-invitation.py [options] setall
  mailchimp-invitation.py [options] get <email> 
  mailchimp-invitation.py -h, --help

Options:
  -c, --code=<code>         
  -l, --list=<list name>    [default: the longaccess news]
  -k, --key=<key>           [default: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxx]

The default values above are the ones we use for our specific environment.
You should change them to fit yours.

Source: http://github.com/longaccess/misc-tools
License: Apache License Version 2.0
"""

import sys
from docopt import docopt
import hashlib
import mailchimp

args = docopt(__doc__)

APIKEY = args['--key']
if not APIKEY:
    print 'No API KEY given. Please use "--key".\nVisit https://admin.mailchimp.com/account/api/ to generate one.'
    sys.exit(1)
mc = mailchimp.Mailchimp(APIKEY)

def invcode(email):
    m = hashlib.md5()
    m.update('%s-set-your-own-secret-here' % email )
    code = m.hexdigest()[:6]
    return code

def getListID(list_name):
    # Get list ID by name.
    lists = mc.lists.list( filters = { 'list_name' : list_name } )
    if lists['total']:
        list_id = lists['data'][0]['id']
        return list_id
    else:
        print 'Error: List "%s" not found.' % args['--list']
        sys.exit(1)

def getGroupID(group_name, list_name=None, list_id=None):
    if not list_id:
        list_id = getListID(list_name)
    ret=mc.lists.interest_groupings(id=list_id)
    if 'status' in ret and ret['status'] == 'error':
        for e in ret['errors']:
            print e['code'], e['error']
        sys.exit(1)
    for r in ret:
        if group_name in [ g['name'] for g in r['groups'] ]:
            return r['id']

def getEmail(email, list_name=None, listID=None):
    if listID:
        list_id=listID
    else:
        list_id = getListID(list_name)
    rec = mc.lists.member_info(id=list_id, emails=[{'email':email}])
    if rec['error_count']:
        for e in rec['errors']:
            print e['code'], e['error']
        sys.exit(1)
    else:
        return rec['data']

def setInvite(list_name, email, code=None):
    list_id = getListID(list_name)
    e=getEmail(listID=list_id, email=email) #check if email exists.
    if code:
        inv_code=args['--code']
    else:
        inv_code=invcode(args['<email>'])
    upd = mc.lists.subscribe( 
        id=list_id, 
        email={'email': args['<email>']},
        update_existing=True, 
        replace_interests=False,  
        merge_vars={'invcode':inv_code} 
        )
def setGroupInvite(list_name, group_name):
    list_id = getListID(list_name)
    group_id = getGroupID(
        list_id=list_id,
        group_name=args['<group>']
        )
   # Get all members with checked "Software Developer"
    members = mc.lists.members(id=list_id, opts = {
        'limit': 100,
        'segment': {
            'match': 'ALL',
            'conditions': [ {
                'field': 'interests-%s' % group_id,
                'op': 'one',
                'value': 'Software Developer'
            } ]
        }
        })

    print 'Updating %s records.' % members['total']
    total_recs = members['total']
    page = 0
    count = 0
    
    while 100*page < total_recs: 

        # Prepare the batch update data (in batches of 100s)
        batch = []
        for member in members['data']:
            count += 1 
            invite = invcode(member['email'])
            batch.append(
                { 'email': { 'email': member['email']}, 'merge_vars': {'invcode': invite} }
                )
            print '%03d\t%s\t\t%s' % (count, member['email'], invite)
        
        # Batch update list
        upd = mc.lists.batch_subscribe( id=list_id, update_existing=True, replace_interests=False, batch=batch)

        page += 1

        # read next batch.
        members = mc.lists.members(id=list_id, opts = {
            'start': page,
            'limit': 100,
            'segment': {
                'match': 'ALL',
                'conditions': [ {
                    'field': 'interests-%s' % group_id,
                    'op': 'one',
                    'value': 'Software Developer'
                } ]
            }
            })

def setListInvite(list_name):
    list_id = getListID(list_name)
    
    # Get all members of list.
    members = mc.lists.members(
        id=list_id, 
        opts = {
            'limit': 100,
            }
        )
    print 'Updating %s records.' % members['total']
    total_recs = members['total']
    page = 0
    count = 0
    
    while 100*page < total_recs: 
        # Prepare the batch update data (in batches of 100s)
        batch = []
        for member in members['data']:
            count += 1 
            invite = invcode(member['email'])
            batch.append(
                { 'email': { 'email': member['email']}, 'merge_vars': {'invcode': invite} }
                )
            print '%03d\t%s\t\t%s' % (count, member['email'], invite)
        # Batch update list
        upd = mc.lists.batch_subscribe( id=list_id, update_existing=True, replace_interests=False, batch=batch)
        page += 1
        # read next batch.
        members = mc.lists.members(
            id=list_id, 
            opts = {
                'start': page,
                'limit': 100,
            }
        )

if args['set']:
        setInvite(
            list_name=args['--list'],
            email=args['<email>'],
            code=args['--code']
            )
elif args['setgroup']:
    setGroupInvite(
        list_name=args['--list'],
        group_name=args['<group>']
        )
elif args['setall']:
    setListInvite(
        list_name=args['--list']
        )
elif args['get']:
    rec = getEmail(
        list_name=args['--list'],
        email=args['<email>']
        )
    print "%s\t%s" % (
            rec[0]['email'],
            rec[0]['merges']['INVCODE']
            )
