from django import forms

from .models import Dataset


class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset

        fields = (
            'title',
            'file',
        )

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'placeholder': (
                        'اكتب اسمًا واضحًا للملف'
                    ),
                },
            ),

            'file': forms.ClearableFileInput(
                attrs={
                    'accept': '.xlsx,.xls,.xlsm',
                },
            ),
        }

    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):
        self.user = user

        super().__init__(
            *args,
            **kwargs,
        )

    def clean_file(self):
        uploaded_file = self.cleaned_data.get(
            'file'
        )

        if not uploaded_file:
            return uploaded_file

        limit_mb = 10

        if (
            self.user
            and hasattr(
                self.user,
                'profile',
            )
        ):
            limit_mb = (
                self.user
                .profile
                .max_file_size_mb
            )

        maximum_bytes = (
            limit_mb
            * 1024
            * 1024
        )

        if uploaded_file.size > maximum_bytes:
            raise forms.ValidationError(
                f'الحد الأقصى المسموح لحسابك '
                f'هو {limit_mb} ميجابايت.'
            )

        return uploaded_file