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


class SingleRecipeForm(FlaskForm):
    '''
    single recipe in a nutrition log
    '''
    recipe_id = HiddenField(validators=[val.DataRequired()])
    selected = BooleanField()


class EditLogForm(FlaskForm):
    recipes = FieldList(FormField(SingleRecipeForm), min_entries=0)
    submit = SubmitField('Save Changes')

    def populate_entries(self, entries):
        '''
        populates the form with recipe entries
        '''
        self.recipes.entries = []
        for _, recipe_id, *_ in entries:
            form = SingleRecipeForm()
            form.recipe_id.data = recipe_id
            self.recipes.append_entry(form)

    def get_selected_ids(self):
        '''
        gets the recipe ids for all displayed recipes
        '''
        return [
            entry.recipe_id.data
            for entry in self.recipes
            if entry.selected.data
        ]
