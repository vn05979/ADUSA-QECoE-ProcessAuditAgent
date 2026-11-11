"""Single-file Django app for the ADUSA-QECoE-ProcessAuditAgent UI.

Run:  python ui/app.py runserver
"""
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import execute_from_command_line

UI_DIR = Path(__file__).resolve().parent
REPO_DIR = UI_DIR.parent
UPLOAD_DIR = UI_DIR / "uploads"

APP_NAME = "ADUSA-QECoE-ProcessAuditAgent"

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="dev-only-insecure-key-change-me",
        ALLOWED_HOSTS=["localhost", "127.0.0.1"],
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=["django.contrib.staticfiles"],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
        ],
        SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [UI_DIR / "templates"],
                "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
            }
        ],
        STATIC_URL="static/",
        STATICFILES_DIRS=[REPO_DIR / "images"],
    )

from django import forms  # noqa: E402
from django.shortcuts import redirect, render  # noqa: E402
from django.urls import path  # noqa: E402
from django.utils.text import get_valid_filename  # noqa: E402


class ProjectForm(forms.Form):
    project_name = forms.CharField(
        label="Project name",
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "PRJ followed by 5 digits (e.g., PRJ12345)", "autofocus": True}),
    )

    def clean_project_name(self):
        name = self.cleaned_data["project_name"].strip()
        if not name:
            raise forms.ValidationError("Project name is required.")
        if not re.fullmatch(r"PRJ[0-9]{5}", name):
            raise forms.ValidationError("Enter a project name in the format PRJXXXXX (PRJ followed by 5 digits).")
        return name


class SourceForm(forms.Form):
    SHAREPOINT = "sharepoint"
    ZIP = "zip"

    source = forms.ChoiceField(
        label="Choose how to provide project artifacts",
        choices=[(SHAREPOINT, "Enter SharePoint URL"), (ZIP, "Upload ZIP file")],
        widget=forms.RadioSelect,
        initial=SHAREPOINT,
    )
    sharepoint_url = forms.URLField(
        label="SharePoint URL",
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://aholddelhaize.sharepoint.com/sites/RBSQA/<project>"}),
    )
    zip_file = forms.FileField(
        label="ZIP file",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": ".zip"}),
    )

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get("source")
        if source == self.SHAREPOINT:
            url = cleaned.get("sharepoint_url")
            if not url:
                self.add_error("sharepoint_url", "Please enter the SharePoint URL.")
            elif not url.startswith("https://aholddelhaize.sharepoint.com/sites/RBSQA/"):
                self.add_error(
                    "sharepoint_url",
                    "Enter a URL starting with https://aholddelhaize.sharepoint.com/sites/RBSQA/.",
                )
        elif source == self.ZIP:
            upload = cleaned.get("zip_file")
            if not upload:
                self.add_error("zip_file", "Please choose a ZIP file to upload.")
            elif not upload.name.lower().endswith(".zip") or not zipfile.is_zipfile(upload):
                self.add_error("zip_file", "The selected file is not a valid ZIP archive.")
            else:
                upload.seek(0)
        return cleaned


def save_upload(upload):
    UPLOAD_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target = UPLOAD_DIR / f"{stamp}_{get_valid_filename(upload.name)}"
    with target.open("wb") as fh:
        for chunk in upload.chunks():
            fh.write(chunk)
    return target


def home(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            request.session["project_name"] = form.cleaned_data["project_name"]
            return redirect("source")
    else:
        form = ProjectForm(initial={"project_name": request.session.get("project_name", "")})
    return render(request, "index.html", {"app_name": APP_NAME, "form": form})


def source(request):
    project_name = request.session.get("project_name")
    if not project_name:
        return redirect("home")

    submitted = None
    if request.method == "POST":
        form = SourceForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data["source"] == SourceForm.SHAREPOINT:
                submitted = {"type": "SharePoint URL", "value": form.cleaned_data["sharepoint_url"]}
            else:
                saved = save_upload(form.cleaned_data["zip_file"])
                submitted = {"type": "ZIP file", "value": saved.name}
            request.session["project_source"] = submitted
            form = SourceForm()
    else:
        form = SourceForm()

    return render(
        request,
        "source.html",
        {"app_name": APP_NAME, "project_name": project_name, "form": form, "submitted": submitted},
    )


urlpatterns = [
    path("", home, name="home"),
    path("source/", source, name="source"),
]


if __name__ == "__main__":
    execute_from_command_line(sys.argv)