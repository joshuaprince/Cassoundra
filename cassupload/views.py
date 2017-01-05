from django.shortcuts import render
from django.http import HttpResponseRedirect

from .forms import UploadFileForm


def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/upload/success')
    else:
        form = UploadFileForm()
    return render(request, 'cassupload/upload.html', {'form': form})
