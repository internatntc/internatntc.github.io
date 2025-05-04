from django import forms
from django.contrib.auth import get_user_model
from rbac.models import UserProfile, Role, UserRole

User = get_user_model()


class CreateUserForm(forms.ModelForm):
    middle_name = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    role = forms.ModelChoiceField(queryset=Role.objects.all())
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Create profile
            UserProfile.objects.create(
                user=user,
                middle_name=self.cleaned_data['middle_name'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address']
            )
            # Assign role
            UserRole.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
        return user
