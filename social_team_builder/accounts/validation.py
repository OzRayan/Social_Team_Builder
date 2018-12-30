regex = {
    '[A-Z]': 'Password must contain at least one upper letter!',
    '[a-z]': 'Password must contain at least one lower letter!',
    '\d': 'Password must contain at least one number!',
    '\W[^_]': 'Password must contain at least one special character (ex: .\!@#$%^&*?_~-)'
}

error_msg = {
    'a': 'First give the old password!',
    'b': 'Before confirming the new password, add one first!',
    'c': 'Confirm the new password',
    'd': 'Minim length 14 characters!',
    'e': 'Passwords doesn\'t match!',
    'f': 'Password can\'t contain your first or last name!',
    'g': 'New password can\'t match with the old password!'
}