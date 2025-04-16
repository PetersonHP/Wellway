'''
Forms related to user registration and login
'''

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, \
    IntegerField, FieldList, FormField, SubmitField, BooleanField, \
    HiddenField
from wtforms import validators as val


class RegistrationForm(FlaskForm):
    '''
    form to register a new user
    '''
    username = StringField(
        'Username', validators=[val.DataRequired(),
                                val.Length(min=4, max=30,
                                           message='Must be between 4 and 30 characters.')]
    )
    email = StringField(
        'Email', validators=[val.DataRequired(),
                             val.Length(
                                 min=6, max=40, message='Must be between 6 and 40 characters.'),
                             val.Email(message='Invalid email address.')]
    )
    password = PasswordField(
        'Password', validators=[val.DataRequired(),
                                val.Length(min=6, max=40, message='Must be between 6 and 40 characters.')]
    )
    confirm = PasswordField(
        'Confirm Password',
        [val.DataRequired(),
         val.EqualTo('password', message='Passwords must match exactly')]
    )


class LoginForm(FlaskForm):
    '''
    form to login an existing user
    '''
    username = StringField('Username', [val.DataRequired()])
    password = PasswordField('Password', [val.DataRequired()])


class ForgotPasswordForm(FlaskForm):
    '''
    form for a user who forgot their password
    '''
    email = StringField(
        'Email', validators=[val.DataRequired(),
                             val.Length(min=6, max=40),
                             val.Email(message='Invalid email address.')]
    )


class AddFoodFormItem(FlaskForm):
    '''
    A single recipe item to add
    '''
    class Meta:
        csrf = False

    quantity = IntegerField('Quantity', default=0, validators=[
        val.NumberRange(min=0, message="Quantity must be a positive, non-decimal number.")]
    )


class AddFoodForm(FlaskForm):
    '''
    Form to add new foods to the log
    '''
    items = FieldList(FormField(AddFoodFormItem), min_entries=1)

    def add_item(self):
        '''
        Add recipe item to form
        '''
        self.items.append_entry()


class EditLogFormItem(FlaskForm):
    '''
    single recipe in a nutrition log to edit
    '''

    class Meta:
        csrf = False

    recipe_id = HiddenField(val.DataRequired())
    selected = BooleanField()


class EditLogForm(FlaskForm):
    '''
    form to remove foods from log
    '''
    recipes = FieldList(FormField(EditLogFormItem), min_entries=0)

    def add_item(self, id):
        '''
        Add recipe item to form
        '''
        new_entry = self.recipes.append_entry()
        new_entry.recipe_id.data = id

    # def get_selected_ids(self):
    #     '''
    #     gets the recipe ids for all displayed recipes
    #     '''

    #     # DEBUG
    #     # print(f'FOUND: {[entry.form.recipe_id.data for entry in self.recipes 
    #     # if entry.form.selected.data]}')
    #     print(self.recipes[0].form.selected.data)

    #     return [
    #         entry.form.recipe_id.data
    #         for entry in self.recipes
    #         if entry.form.selected.data
    #     ]
