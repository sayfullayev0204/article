from django import forms
from app.models import Author

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Parol")

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Parol")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Parolni tasdiqlash")

    class Meta:
        model = Author
        fields = ['given_name', 'family_name', 'email', 'country', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Parollar mos kelmaydi!")
        return cleaned_data

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['given_name', 'family_name', 'preferred_name', 'email', 'country', 
                  'homepage', 'orcid', 'bio', 'affiliation', 'role']