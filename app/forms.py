from .models import File
from django import forms

class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('file',)