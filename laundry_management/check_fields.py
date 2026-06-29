print("USER FIELDS:", [k for k in env['res.users']._fields.keys() if 'group' in k])
print("GROUP FIELDS:", [k for k in env['res.groups']._fields.keys() if 'user' in k])
