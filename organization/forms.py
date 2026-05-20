from django import forms
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from .models import Campus


class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ['name', 'address', 'phone', 'manager', 'is_active']
        labels = {
            'name': '校区名称',
            'address': '地址',
            'phone': '联系电话',
            'manager': '校区长',
            'is_active': '启用状态',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields['manager'].queryset = User.objects.filter(
            profile__role=UserProfile.ROLE_CAMPUS_MANAGER,
        ).order_by('username')
        self.fields['manager'].required = False
        self.fields['manager'].empty_label = '暂不指定'
