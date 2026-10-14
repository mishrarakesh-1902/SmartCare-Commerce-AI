from django.db import models

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
import datetime




# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name
 
class Sub_category(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category , on_delete=models.CASCADE )


    def __str__(self):
        return self.name

#brand models to fetch database 
 
class Brand(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    
class Product(models.Model):
    Availability = (('In Stock' , 'In Stock') , ('Out of Stock' , 'Out of Stock'))

    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False, default='')
    sub_category= models.ForeignKey(Sub_category, on_delete=models.CASCADE , null=False, default='')
    brand = models.ForeignKey(Brand , on_delete=models.CASCADE ,null=True)
    image = models.ImageField(upload_to='ecommerce/pimg')
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    Availability = models.CharField(choices=Availability, null=True , max_length=1000)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required = True , label='Email' , error_messages={'exists': 'This Already Exists'})

    class Meta:
        model = User
        fields = ('username' , 'email', 'password1','password2')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adding placeholders and CSS classes to each field
        self.fields['username'].widget.attrs.update({'placeholder': 'User Name', 'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email Address', 'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password', 'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password', 'class': 'form-control'})    


        def save(self, commit=True):
            user = super(UserCreateForm,self).save(commit=False)
            user.email= self.cleaned_data['email']
            if commit:
                user.save()
            return user
        
        def clean_email(self):
            if User.objects.filter(email=self.cleaned_data['email']).exists():
                raise forms.ValidationError(self.fields['email'].error_message['exists'])
            return self.cleaned_data['email']
        


class Contact_us(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()


    def __str__(self):
        return self.email
    


class Order(models.Model):
    image = models.ImageField(upload_to='ecommerce/order/image')
    product = models.CharField(max_length=1000 , default='')
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    price = models.IntegerField()
    quantity = models.CharField(max_length=5)
    total = models.CharField(max_length=10000000 , default='')
    address = models.TextField()
    phone = models.CharField(max_length=10)
    pincode = models.CharField(max_length=10)
    
    date = models.DateField(default=datetime.datetime.today)
    

    def __str__(self):
        return self.product
    




class Feedback(models.Model):
    brand_name = models.CharField(max_length=100)
    product_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.IntegerField(choices=[(1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐')])
    comments = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.brand_name} - {self.rating} Stars"


class SupportTicket(models.Model):
    ticket_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    urgency = models.CharField(max_length=50, blank=True, null=True)
    sentiment = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=100, blank=True, null=True)
    ai_response = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='resolved')
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.subject} ({self.status})"
