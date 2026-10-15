from django.contrib import admin
from .models import Category,Sub_category,Product,ProductImage,Contact_us,Order,Brand,SupportTicket,Feedback,UserProfile

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'alt_text', 'order')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sub_category', 'brand', 'price', 'Availability')
    list_filter = ('category', 'sub_category', 'brand', 'Availability')
    search_fields = ('name',)
    inlines = [ProductImageInline]

admin.site.register(ProductImage)

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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'state', 'pincode', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'address', 'city', 'pincode')