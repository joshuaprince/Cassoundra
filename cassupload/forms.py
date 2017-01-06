from django import forms
from .models import Sound


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = Sound
        fields = ['file', 'name', 'loud']
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.mp3'}),
        }
