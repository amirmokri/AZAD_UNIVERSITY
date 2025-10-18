"""
Django forms for validation and user input handling
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import ClassSchedule, Teacher, Course, Room


class ClassScheduleForm(forms.ModelForm):
    """
    Form for creating and editing ClassSchedule instances.
    
    Uses the new start_time and end_time fields as primary inputs,
    with time_slot as a fallback for backward compatibility.
    """
    
    class Meta:
        model = ClassSchedule
        fields = [
            'course', 'teacher', 'room', 'day_of_week', 
            'start_time', 'end_time', 'time_slot',
            'semester', 'academic_year', 'notes', 
            'is_holding', 'is_active'
        ]
        widgets = {
            'day_of_week': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'روز هفته را انتخاب کنید'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'placeholder': 'ساعت شروع (مثال: 07:30)'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control',
                'placeholder': 'ساعت پایان (مثال: 09:15)'
            }),
            'time_slot': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'بازه زمانی (اختیاری - قدیمی)'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control'
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-control'
            }),
            'room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'semester': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نیمسال تحصیلی'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'سال تحصیلی'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'یادداشت‌ها (اختیاری)'
            }),
            'is_holding': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'course': 'درس',
            'teacher': 'استاد',
            'room': 'اتاق',
            'day_of_week': 'روز هفته',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان',
            'time_slot': 'بازه زمانی (قدیمی)',
            'semester': 'نیمسال',
            'academic_year': 'سال تحصیلی',
            'notes': 'یادداشت‌ها',
            'is_holding': 'کلاس برگزار می‌شود',
            'is_active': 'فعال'
        }
        help_texts = {
            'start_time': 'ساعت شروع کلاس (مثال: 07:30)',
            'end_time': 'ساعت پایان کلاس (مثال: 09:15)',
            'time_slot': 'بازه زمانی قدیمی - به صورت خودکار از ساعت شروع و پایان محاسبه می‌شود',
            'is_holding': 'آیا این کلاس در حال حاضر برگزار می‌شود؟',
            'is_active': 'آیا این برنامه فعال است؟'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make time_slot field optional and less prominent
        self.fields['time_slot'].required = False
        self.fields['time_slot'].widget.attrs.update({
            'style': 'opacity: 0.7;',
            'title': 'این فیلد قدیمی است - از ساعت شروع و پایان استفاده کنید'
        })
        
        # Make start_time and end_time more prominent
        self.fields['start_time'].required = False  # Will be validated in clean()
        self.fields['end_time'].required = False    # Will be validated in clean()
        
        # Order fields for better UX
        self.field_order = [
            'course', 'teacher', 'room', 'day_of_week',
            'start_time', 'end_time', 'time_slot',
            'semester', 'academic_year', 'notes',
            'is_holding', 'is_active'
        ]
    
    def clean(self):
        """
        Validate the form data.
        
        Ensures that either start_time/end_time or time_slot is provided,
        and validates time conflicts.
        """
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        time_slot = cleaned_data.get('time_slot')
        day_of_week = cleaned_data.get('day_of_week')
        room = cleaned_data.get('room')
        teacher = cleaned_data.get('teacher')
        
        # Validate that we have timing information
        if not (start_time and end_time) and not time_slot:
            raise ValidationError({
                'start_time': 'لطفاً ساعت شروع و پایان کلاس را مشخص کنید.',
                'end_time': 'لطفاً ساعت شروع و پایان کلاس را مشخص کنید.'
            })
        
        # Validate time logic
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError({
                    'end_time': 'ساعت پایان باید بعد از ساعت شروع باشد.'
                })
        
        # Check for conflicts using the model's validation
        if self.instance.pk:
            # For updates, temporarily set the fields to check conflicts
            original_start = self.instance.start_time
            original_end = self.instance.end_time
            original_time_slot = self.instance.time_slot
            
            if start_time and end_time:
                self.instance.start_time = start_time
                self.instance.end_time = end_time
            elif time_slot:
                self.instance.time_slot = time_slot
            
            try:
                self.instance.clean()
            except ValidationError as e:
                # Restore original values
                self.instance.start_time = original_start
                self.instance.end_time = original_end
                self.instance.time_slot = original_time_slot
                raise e
            finally:
                # Restore original values
                self.instance.start_time = original_start
                self.instance.end_time = original_end
                self.instance.time_slot = original_time_slot
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the form instance.
        
        Automatically populates time_slot from start_time/end_time if not set.
        """
        instance = super().save(commit=False)
        
        # Auto-populate time_slot from start_time/end_time if not set
        if instance.start_time and instance.end_time and not instance.time_slot:
            time_slot_value = f"{instance.start_time.strftime('%H:%M')}-{instance.end_time.strftime('%H:%M')}"
            # Only set if it matches one of the predefined choices
            if time_slot_value in [choice[0] for choice in ClassSchedule.TIME_CHOICES]:
                instance.time_slot = time_slot_value
        
        if commit:
            instance.save()
        
        return instance


class ClassScheduleSearchForm(forms.Form):
    """
    Form for searching and filtering ClassSchedule instances.
    """
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True).order_by('course_code'),
        required=False,
        empty_label="همه دروس",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.filter(is_active=True).order_by('full_name'),
        required=False,
        empty_label="همه اساتید",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True).order_by('room_number'),
        required=False,
        empty_label="همه اتاق‌ها",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    day_of_week = forms.ChoiceField(
        choices=[('', 'همه روزها')] + ClassSchedule.DAY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': 'از ساعت'
        })
    )
    
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': 'تا ساعت'
        })
    )
    
    is_holding = forms.ChoiceField(
        choices=[
            ('', 'همه وضعیت‌ها'),
            ('true', 'برگزار می‌شود'),
            ('false', 'برگزار نمی‌شود')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'همه وضعیت‌ها'),
            ('true', 'فعال'),
            ('false', 'غیرفعال')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجو در نام درس، استاد یا اتاق...'
        })
    )
    
    labels = {
        'course': 'درس',
        'teacher': 'استاد',
        'room': 'اتاق',
        'day_of_week': 'روز هفته',
        'start_time': 'از ساعت',
        'end_time': 'تا ساعت',
        'is_holding': 'وضعیت برگزاری',
        'is_active': 'وضعیت فعال',
        'search': 'جستجو'
    }