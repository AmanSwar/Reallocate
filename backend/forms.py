from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, MultipleFileField
from wtforms.validators import DataRequired

class ProductUploadForm(FlaskForm):
    product_name = StringField('Product Name', validators=[DataRequired()])
    product_images = MultipleFileField('Upload Images', validators=[DataRequired()])
    product_videos = MultipleFileField('Upload Videos')
    submit = SubmitField('Upload Product')
