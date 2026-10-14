from django.contrib import admin
from .models import Category,Sub_category,Product,Contact_us,Order,Brand,SupportTicket,Feedback

admin.site.register(Category)
admin.site.register(Sub_category)
admin.site.register(Product)
admin.site.register(Contact_us)
admin.site.register(Order)
admin.site.register(Brand)
admin.site.register(Feedback)

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'name', 'category', 'urgency', 'sentiment', 'action', 'status', 'email_sent', 'created_at')
    list_filter = ('category', 'urgency', 'sentiment', 'status', 'email_sent')
    search_fields = ('ticket_id', 'name', 'email', 'subject', 'message', 'order_id')
    readonly_fields = ('ticket_id', 'created_at')