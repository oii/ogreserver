from __future__ import absolute_import

from flask.ext.wtf import Form

from wtforms import BooleanField, SelectField, validators
from wtforms.fields.html5 import EmailField


class ProfileEditForm(Form):
    email = EmailField('Email Address', [validators.Required(), validators.Email()])
    preferred_ebook_format = SelectField(
        'Preferred Ebook Format',
        choices=[('mobi', '.mobi'), ('epub', '.epub')],
    )
    dont_email_me = BooleanField("Don't email me ever")
