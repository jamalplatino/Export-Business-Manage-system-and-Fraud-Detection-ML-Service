from django.contrib import admin
from .models import Customer, CustomerNote  # update this import

@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_by', 'created_at')
    list_filter = ('created_by',)
    search_fields = ('customer__name', 'body')
    
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'country', 'created_at')
    search_fields = ('name', 'email')