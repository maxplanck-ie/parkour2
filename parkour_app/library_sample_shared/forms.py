from django import forms
from .models import IndexType


class IndexTypeForm(forms.ModelForm):
    def clean(self):
        indices_i7 = self.cleaned_data.get('indices_i7').all()
        indices_i5 = self.cleaned_data.get('indices_i5').all()

        # Don't allow to choose indices, belonging to another Index Type
        for index_i7 in indices_i7:
            try:
                index_type = index_i7.index_type.get()
            except IndexType.DoesNotExist:
                pass
            else:
                if not self.instance.pk or (self.instance.pk and
                                            self.instance.pk != index_type.pk):
                    raise forms.ValidationError('Index %s belongs to %s.' % (
                        index_i7.index_id, index_type.name,
                    ))

        for index_i5 in indices_i5:
            try:
                index_type = index_i5.index_type.get()
            except IndexType.DoesNotExist:
                pass
            else:
                if not self.instance.pk or (self.instance.pk and
                                            self.instance.pk != index_type.pk):
                    raise forms.ValidationError('Index %s belongs to %s.' % (
                        index_i5.index_id, index_type.name,
                    ))
